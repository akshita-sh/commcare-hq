from datetime import datetime
import logging
from couchdbkit.exceptions import ResourceConflict
from django.conf import settings
from django.db import models
from couchdbkit.ext.django.schema import Document, StringProperty,\
    BooleanProperty, DateTimeProperty, IntegerProperty, DocumentSchema, SchemaProperty
from dimagi.utils.timezones import fields as tz_fields

class DomainMigrations(DocumentSchema):
    has_migrated_permissions = BooleanProperty(default=False)

    def apply(self, domain):
        if not self.has_migrated_permissions:
            logging.info("Applying permissions migration to domain %s" % domain.name)
            from corehq.apps.users.models import UserRole, WebUser
            UserRole.init_domain_with_presets(domain.name)
            for web_user in WebUser.by_domain(domain.name):
                try:
                    web_user.save()
                except ResourceConflict:
                    # web_user has already been saved by another thread in the last few seconds
                    pass

            self.has_migrated_permissions = True
            domain.save()

class Domain(Document):
    """Domain is the highest level collection of people/stuff
       in the system.  Pretty much everything happens at the
       domain-level, including user membership, permission to
       see data, reports, charts, etc."""

    name = StringProperty()
    is_active = BooleanProperty()
    is_public = BooleanProperty(default=False)
    date_created = DateTimeProperty()
    default_timezone = StringProperty(default=getattr(settings, "TIME_ZONE", "UTC"))
    case_sharing = BooleanProperty(default=False)
    
    # domain metadata
    city = StringProperty()
    country = StringProperty()
    region = StringProperty() # e.g. US, LAC, SA, Sub-saharn Africa, East Africa, West Africa, Southeast Asia)
    project_type = StringProperty() # e.g. MCH, HIV
    customer_type = StringProperty() # plus, full, etc.
    is_test = BooleanProperty(default=False)

    migrations = SchemaProperty(DomainMigrations)

    @classmethod
    def wrap(cls, data):
        self = super(Domain, cls).wrap(data)
        if self.get_id:
            self.apply_migrations()
        return self

    @staticmethod
    def active_for_user(user, is_active=True):
        if not hasattr(user,'get_profile'):
            # this had better be an anonymous user
            return []
        from corehq.apps.users.models import CouchUser
        couch_user = CouchUser.from_django_user(user)
        if couch_user:
            domain_names = couch_user.get_domains()
            def log(json):
                doc = json['doc']
                return Domain.wrap(doc)
            return Domain.view("domain/by_status",
                                    keys=[[is_active, d] for d in domain_names],
                                    reduce=False,
                                    wrapper=log,
                                    include_docs=True).all()
        else:
            return []

    def apply_migrations(self):
        self.migrations.apply(self)

    @staticmethod
    def all_for_user(user):
        if not hasattr(user,'get_profile'):
            # this had better be an anonymous user
            return []
        from corehq.apps.users.models import CouchUser
        couch_user = CouchUser.from_django_user(user)
        if couch_user:
            domain_names = couch_user.get_domains()
            return Domain.view("domain/domains",
                                    keys=domain_names,
                                    reduce=False,
                                    include_docs=True).all()
        else:
            return []

    def add(self, model_instance, is_active=True):
        """
        Add something to this domain, through the generic relation.
        Returns the created membership object
        """
        # Add membership info to Couch
        couch_user = model_instance.get_profile().get_couch_user()
        couch_user.add_domain_membership(self.name)
        couch_user.save()

    def __unicode__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name):
        result = cls.view("domain/domains",
                            key=name,
                            reduce=False,
                            include_docs=True).first()
        return result

    @classmethod
    def get_or_create_with_name(cls, name, is_active=False):
        result = cls.view("domain/domains",
            key=name,
            reduce=False,
            include_docs=True).first()
        if result:
            return result
        else:
            new_domain = Domain(name=name,
                            is_active=is_active,
                            date_created=datetime.utcnow())
            new_domain.save()
            return new_domain

    @classmethod
    def get_all(cls):
        return Domain.view("domain/domains",
                            reduce=False,
                            include_docs=True).all()

##############################################################################################################
#
# Originally had my own hacky global storage of content type, but it turns out that contenttype.models
# wisely caches content types! No hit to the db beyond the first call - no need for us to do our own 
# custom caching.
#
# See ContentType.get_for_model() code for details.

class OldDomain(models.Model):
    """Domain is the highest level collection of people/stuff
       in the system.  Pretty much everything happens at the 
       domain-level, including user membership, permission to 
       see data, reports, charts, etc."""

    name  = models.CharField(max_length = 64, unique=True)
    is_active = models.BooleanField(default=False)
    timezone = tz_fields.TimeZoneField()
    #description = models.CharField(max_length=255, null=True, blank=True)
    #timezone = models.CharField(max_length=64,null=True)

    class Meta():
        db_table = "domain_domain"
    
    # Utility function - gets active domains in which user has an active membership 
    # Note that User.is_active is not checked here - we're only concerned about usable
    # domains in which the user can theoretically participate, not whether the user 
    # is cleared to login.

    @staticmethod
    def active_for_user(user):
        if not hasattr(user,'get_profile'):
            # this had better be an anonymous user
            return OldDomain.objects.none()
        from corehq.apps.users.models import CouchUser
        couch_user = CouchUser.from_django_user(user)
        if couch_user:
            domain_names = couch_user.get_domains()
            return OldDomain.objects.filter(name__in=domain_names, is_active=True)
        else:
            return OldDomain.objects.none()

    @staticmethod
    def all_for_user(user):
        if not hasattr(user,'get_profile'):
            # this had better be an anonymous user
            return OldDomain.objects.none()
        from corehq.apps.users.models import CouchUser
        couch_user = CouchUser.from_django_user(user)
        if couch_user:
            domain_names = couch_user.get_domains()
            return OldDomain.objects.filter(name__in=domain_names)
        else:
            return OldDomain.objects.none()
    
    def add(self, model_instance, is_active=True):
        """
        Add something to this domain, through the generic relation.
        Returns the created membership object
        """
        # Add membership info to Couch
        couch_user = model_instance.get_profile().get_couch_user()
        couch_user.add_domain_membership(self.name)
        couch_user.save()
        
    def __unicode__(self):
        return self.name
