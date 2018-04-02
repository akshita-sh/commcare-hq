from __future__ import absolute_import
from __future__ import unicode_literals

from django.test import SimpleTestCase

from corehq.apps.app_manager.models import Application, TrainingModule
from corehq.apps.app_manager.tests.util import TestXmlMixin


class ShadowModuleSuiteTest(SimpleTestCase, TestXmlMixin):

    def test_training_module(self):
        app = Application.new_app('domain', 'Untitled Application')
        training_module = app.add_module(TrainingModule.new_module('training module', None))
        app.new_form(training_module.id, "Untitled Form", None)
        self.assertXmlPartialEqual(
            """
            <partial>
                <menu root="training-root" id="m0">
                    <text>
                        <locale id="modules.m0"/>
                    </text>
                    <command id="m0-f0"/>
                </menu>
            </partial>
            """,
            app.create_suite(),
            "./menu"
        )
