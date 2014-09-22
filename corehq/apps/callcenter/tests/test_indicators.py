from collections import namedtuple
from casexml.apps.case.mock import CaseBlock
from casexml.apps.case.xml import V2
from corehq.apps.callcenter.indicator_sets import AAROHI_MOTHER_FORM, CallCenterIndicators, cache_key, CachedIndicators
from corehq.apps.callcenter.utils import sync_user_cases
from corehq.apps.domain.shortcuts import create_domain
from corehq.apps.callcenter.tests.sql_fixture import load_data, load_custom_data, clear_data
from corehq.apps.groups.models import Group
from corehq.apps.hqcase.utils import submit_case_blocks, get_case_by_domain_hq_user_id
from corehq.apps.users.models import CommCareUser
from django.test import TestCase

from django.core import cache
from mock import patch

locmem_cache = cache.get_cache('django.core.cache.backends.locmem.LocMemCache')


def patch_local_cache(module, varname):
    locmem_cache = cache.get_cache('django.core.cache.backends.locmem.LocMemCache')
    locmem_cache.clear()
    return patch.object(module, varname, locmem_cache)


def create_domain_and_user(domain_name, username):
    domain = create_domain(domain_name)
    user = CommCareUser.create(domain_name, username, '***')

    domain.call_center_config.enabled = True
    domain.call_center_config.case_owner_id = user.user_id
    domain.call_center_config.case_type = 'cc_flw'
    domain.save()

    sync_user_cases(user)
    return domain, user


def create_cases_for_types(domain, case_types):
    for i, case_type in enumerate(case_types):
        submit_case_blocks(
            CaseBlock(
                create=True,
                case_id='person%s' % i,
                case_type=case_type,
                user_id='user%s' % i,
                version=V2,
            ).as_string(), domain)


def get_indicators(prefix, values, infix=None, is_legacy=False):
    ranges = ['week0', 'week1', 'month0', 'month1']
    data = {}
    separator = '' if is_legacy else '_'
    infix = '{}{}{}'.format(separator, infix, separator) if infix else separator
    for i, r in enumerate(ranges):
        r = r.title() if is_legacy else r
        indicator_name = '{prefix}{infix}{suffix}'.format(
            prefix=prefix,
            infix=infix,
            suffix=r)
        data[indicator_name] = values[i]

    return data


StaticIndicators = namedtuple('StaticIndicators', 'name, values, is_legacy, infix')


def expected_standard_indicators(no_data=False):
    expected = {'totalCases': 0L if no_data else 5L}
    expected_values = [
        StaticIndicators('formsSubmitted', [2L, 4L, 7L, 0L], True, None),
        StaticIndicators('forms_submitted', [2L, 4L, 7L, 0L], False, None),
        StaticIndicators('casesUpdated', [0L, 1L, 3L, 5L], True, None),
        StaticIndicators('cases_total', [4L, 4L, 6L, 5L], False, None),
        StaticIndicators('cases_opened', [0L, 1L, 3L, 5L], False, None),
        StaticIndicators('cases_closed', [0L, 0L, 2L, 2L], False, None),
        StaticIndicators('cases_active', [0L, 1L, 3L, 5L], False, None),
        StaticIndicators('cases_total', [1L, 1L, 3L, 0L], False, 'person'),
        StaticIndicators('cases_total', [3L, 3L, 3L, 5L], False, 'dog'),
        StaticIndicators('cases_opened', [0L, 1L, 3L, 0L], False, 'person'),
        StaticIndicators('cases_opened', [0L, 0L, 0L, 5L], False, 'dog'),
        StaticIndicators('cases_closed', [0L, 0L, 2L, 0L], False, 'person'),
        StaticIndicators('cases_closed', [0L, 0L, 0L, 2L], False, 'dog'),
        StaticIndicators('cases_active', [0L, 1L, 3L, 0L], False, 'person'),
        StaticIndicators('cases_active', [0L, 0L, 0L, 5L], False, 'dog')
    ]
    for val in expected_values:
        values = [0L] * 4 if no_data else val.values
        expected.update(get_indicators(val.name, values, val.infix, val.is_legacy))

    return expected


class BaseCCTests(TestCase):
    def setUp(self):
        locmem_cache.clear()

    def _test_indicators(self, user, indicator_set, expected):
        data = indicator_set.get_data()
        user_case = get_case_by_domain_hq_user_id(
            user.domain,
            user.user_id,
            include_docs=True
        )
        case_id = user_case.case_id
        self.assertIn(case_id, data)

        user_data = data[case_id]

        mismatches = []
        for k, v in expected.items():
            expected_value = user_data.pop(k, None)
            if expected_value != v:
                mismatches.append('{}: {} != {}'.format(k, v, expected_value))

        if mismatches:
            self.fail('Mismatching indicators:\n{}'.format('\t\n'.join(mismatches)))

        if user_data:
            self.fail('Additional indicators:\n{}'.format('\t\n'.join(user_data.keys())))


class CallCenterTests(BaseCCTests):
    @classmethod
    def setUpClass(cls):
        cls.cc_domain, cls.cc_user = create_domain_and_user('callcentertest', 'user1')
        load_data(cls.cc_domain.name, cls.cc_user.user_id)
        cls.cc_user_no_data = CommCareUser.create(cls.cc_domain.name, 'user3', '***')

        cls.aarohi_domain, cls.aarohi_user = create_domain_and_user('aarohi', 'user2')
        load_custom_data(cls.aarohi_domain.name, cls.aarohi_user.user_id, xmlns=AAROHI_MOTHER_FORM)

        # create one case of each type so that we get the indicators where there is no data for the period
        create_cases_for_types('callcentertest', ['person', 'dog'])

    @classmethod
    def tearDownClass(cls):
        cls.cc_domain.delete()
        cls.aarohi_domain.delete()
        clear_data()

    def check_cc_indicators(self, indicator_set, expected):
        super(CallCenterTests, self)._test_indicators(self.cc_user, indicator_set, expected)
        expected_no_data = expected_standard_indicators(no_data=True)
        super(CallCenterTests, self)._test_indicators(self.cc_user_no_data, indicator_set, expected_no_data)

    def test_standard_indicators(self):
        indicator_set = CallCenterIndicators(self.cc_domain, self.cc_user, custom_cache=locmem_cache)
        self.assertEqual(indicator_set.all_user_ids, set([self.cc_user.get_id, self.cc_user_no_data.get_id]))
        self.assertEqual(indicator_set.users_needing_data, set([self.cc_user.get_id, self.cc_user_no_data.get_id]))
        self.assertEqual(indicator_set.owners_needing_data, set([self.cc_user.get_id, self.cc_user_no_data.get_id]))
        self.check_cc_indicators(indicator_set, expected_standard_indicators())

    def test_custom_indicators(self):
        expected = {'totalCases': 0L}
        expected.update(get_indicators('formsSubmitted', [3L, 3L, 9L, 0L], is_legacy=True))
        expected.update(get_indicators('forms_submitted', [3L, 3L, 9L, 0L]))
        expected.update(get_indicators('casesUpdated', [0L, 0L, 0L, 0L], is_legacy=True))
        expected.update(get_indicators('cases_total', [0L, 0L, 0L, 0L]))
        expected.update(get_indicators('cases_opened', [0L, 0L, 0L, 0L]))
        expected.update(get_indicators('cases_closed', [0L, 0L, 0L, 0L]))
        expected.update(get_indicators('cases_active', [0L, 0L, 0L, 0L]))

        # custom
        expected.update(get_indicators('motherForms', [3L, 3L, 9L, 0L], is_legacy=True))
        expected.update(get_indicators('childForms', [0L, 0L, 0L, 0L], is_legacy=True))
        expected.update(get_indicators('motherDuration', [3L, 4L, 4L, 0L], is_legacy=True))

        self._test_indicators(
            self.aarohi_user,
            CallCenterIndicators(self.aarohi_domain, self.aarohi_user, custom_cache=locmem_cache),
            expected
        )

    def test_caching(self):
        user_case = get_case_by_domain_hq_user_id(self.cc_domain.name, self.cc_user._id, include_docs=True)
        expected_indicators = {'a': 1, 'b': 2}
        cached_data = CachedIndicators(
            user_id=self.cc_user.get_id,
            case_id=user_case.case_id,
            domain=self.cc_domain.name,
            indicators=expected_indicators
        )
        locmem_cache.set(cache_key(self.cc_user.get_id), cached_data.to_json())

        indicator_set = CallCenterIndicators(self.cc_domain, self.cc_user, custom_cache=locmem_cache)
        self.assertEqual(indicator_set.all_user_ids, set([self.cc_user.get_id, self.cc_user_no_data.get_id]))
        self.assertEquals(indicator_set.users_needing_data, set([self.cc_user_no_data.get_id]))
        self.assertEqual(indicator_set.owners_needing_data, set([self.cc_user_no_data.get_id]))
        self.check_cc_indicators(indicator_set, expected_indicators)

    def test_no_cases_owned_by_user(self):
        indicator_set = CallCenterIndicators(self.cc_domain, self.cc_user_no_data, custom_cache=locmem_cache)
        self.assertEqual(indicator_set.all_user_ids, set())
        self.assertEqual(indicator_set.users_needing_data, set())
        self.assertEqual(indicator_set.owners_needing_data, set())
        self.assertEqual(indicator_set.get_data(), {})


class CallCenterCaseSharingTest(BaseCCTests):
    @classmethod
    def setUpClass(cls):
        cls.domain, cls.user = create_domain_and_user('callcentertest_group', 'user4')
        load_data(cls.domain.name, cls.user.user_id)

        # create one case of each type so that we get the indicators where there is no data for the period
        create_cases_for_types('callcentertest_group', ['person', 'dog'])

    @classmethod
    def tearDownClass(cls):
        cls.domain.delete()
        clear_data()

    def test_cases_owned_by_group(self):
        group = Group(
            domain=self.domain.name,
            name='case sharing group',
            case_sharing=True,
            users=[self.user.user_id]
        )
        group.save()
        user_case = get_case_by_domain_hq_user_id(self.domain.name, self.user._id, include_docs=True)
        user_case.owner_id = group.get_id
        user_case.save()

        indicator_set = CallCenterIndicators(self.domain, self.user, custom_cache=locmem_cache)
        self.assertEqual(indicator_set.all_user_ids, set([self.user.get_id]))
        self.assertEqual(indicator_set.users_needing_data, set([self.user.get_id]))
        self.assertEqual(indicator_set.owners_needing_data, set([self.user.get_id, group.get_id]))
        self._test_indicators(self.user, indicator_set, expected_standard_indicators())