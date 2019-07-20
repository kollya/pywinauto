import os
import sys
import subprocess
import time
import unittest
import re
import six
import mock
import ctypes

if sys.platform.startswith("linux"):
    sys.path.append(".")
    from pywinauto.linux.atspi_objects import AtspiAccessible
    from pywinauto.linux.atspi_objects import AtspiDocument
    from pywinauto.linux.atspi_objects import _GError
    from pywinauto.linux.atspi_element_info import AtspiElementInfo
    from pywinauto.linux.atspi_objects import IATSPI
    from pywinauto.linux.application import Application
    from pywinauto.controls.atspiwrapper import AtspiWrapper
    from pywinauto.linux.atspi_objects import GErrorException
    from pywinauto.linux.atspi_objects import _g_str_hash
    from pywinauto.linux.atspi_objects import _g_str_equal
    from pywinauto.linux.atspi_objects import _g_hash_table_new
    from pywinauto.linux.atspi_objects import _g_hash_table_insert
    from pywinauto.linux.atspi_objects import _GStrHashFunc
    from pywinauto.linux.atspi_objects import _GStrEqualFunc
    from pywinauto.linux.atspi_objects import _ghash2dic

app_name = r"gtk_example.py"


def _test_app():
    test_folder = os.path.join(os.path.dirname
                               (os.path.dirname
                                (os.path.dirname
                                 (os.path.abspath(__file__)))),
                               r"apps/Gtk_samples")
    sys.path.append(test_folder)
    return os.path.join(test_folder, app_name)


if sys.platform.startswith("linux"):
    class AtspiElementInfoTests(unittest.TestCase):

        """Unit tests for the AtspiElementInfo class"""

        def get_app(self, name):
            for children in self.desktop_info.children():
                if children.name == name:
                    return children
            else:
                raise Exception("Application not found")

        def setUp(self):
            self.desktop_info = AtspiElementInfo()
            self.app = Application()
            self.app.start("python3.4 " + _test_app())
            time.sleep(1)
            self.app_info = self.get_app(app_name)

        def tearDown(self):
            self.app.kill()

        def test_can_get_desktop(self):
            self.assertEqual(self.desktop_info.control_type, "DesktopFrame")

        def test_can_get_childrens(self):
            apps = [children.name for children in self.desktop_info.children()]
            self.assertTrue(app_name in apps)

        def test_can_get_name(self):
            self.assertEqual(self.desktop_info.name, "main")

        def test_can_get_parent(self):
            parent = self.app_info.parent
            self.assertEqual(parent.control_type, "DesktopFrame")

        def test_can_get_process_id(self):
            self.assertEqual(self.app_info.process_id, self.app.process)

        def test_can_get_class_name(self):
            self.assertEqual(self.app_info.class_name, "Application")

        def test_can_get_control_type_property(self):
            self.assertEqual(self.app_info.control_type, "Application")

        def test_can_get_control_type_of_all_app_descendants(self):
            print(self.app_info.descendants())
            for children in self.app_info.descendants():
                self.assertTrue(children.control_type in IATSPI().known_control_types.keys())

        def test_control_type_equal_class_name(self):
            for children in self.app_info.descendants():
                self.assertEqual(children.control_type, children.class_name)

        def test_can_get_description(self):
            # TODO find a way to add meaningful description to example application
            self.assertEqual(self.app_info.description(), "")

        def test_can_get_framework_id(self):
            dpkg_output = subprocess.check_output(["dpkg", "-s", "libgtk-3-0"]).decode(encoding='UTF-8')
            version_line = None
            for line in dpkg_output.split("\n"):
                if line.startswith("Version"):
                    version_line = line
                    break
            print(version_line)
            if version_line is None:
                raise Exception("Cant get system gtk version")
            version_pattern = "Version:\\s+(\\d+\\.\\d+\\.\\d+).*"
            r_version = re.compile(version_pattern, flags=re.MULTILINE)
            res = r_version.match(version_line)
            gtk_version = res.group(1)
            self.assertEqual(self.app_info.framework_id(), gtk_version)

        def test_can_get_framework_name(self):
            self.assertEqual(self.app_info.framework_name(), "gtk")

        def test_can_get_atspi_version(self):
            # TODO Get atspi version from loaded so
            version = self.app_info.atspi_version()
            self.assertTrue(version in ["2.0", "2.1"], msg="Unexpected AT-SPI version: {}".format(version))

        def test_can_get_rectangle(self):
            app_info = self.get_app(app_name)
            frame = app_info.children()[0]
            filler = frame.children()[0]
            rectangle = filler.rectangle
            self.assertEqual(rectangle.width(), 600)
            self.assertEqual(rectangle.height(), 492)

        def test_can_compare_applications(self):
            app_info = self.get_app(app_name)
            app_info1 = self.get_app(app_name)
            assert app_info == app_info1

        def test_can_compare_desktop(self):
            desktop = AtspiElementInfo()
            desktop1 = AtspiElementInfo()
            assert desktop == desktop1

        def test_can_get_layer(self):
            self.assertEqual(self.desktop_info.get_layer(), 3)

        def test_can_get_state_set(self):
            frame_info = self.app_info.children()[0]
            states = frame_info.get_state_set()
            self.assertIn('STATE_VISIBLE', states)

        def test_visible(self):
            frame_info = self.app_info.children()[0]
            self.assertTrue(frame_info.visible)

        def test_enabled(self):
            frame_info = self.app_info.children()[0]
            self.assertTrue(frame_info.enabled)

    class AtspiElementInfoDocumentMockedTests(unittest.TestCase):

        """Mocked unit tests for the AtspiElementInfo.document related functionality"""

        def setUp(self):
            self.info = AtspiElementInfo()
            self.patch_get_role = mock.patch.object(AtspiAccessible, 'get_role')
            self.mock_get_role = self.patch_get_role.start()
            self.mock_get_role.return_value = IATSPI().known_control_types["DocumentFrame"]

        def tearDown(self):
            self.patch_get_role.stop()

        def test_document_success(self):
            self.assertEqual(type(self.info.document), AtspiDocument)

        def test_document_fail_on_wrong_role(self):
            self.mock_get_role.return_value = IATSPI().known_control_types["Invalid"]
            self.assertRaises(AttributeError, lambda: self.info.document)

        @mock.patch.object(AtspiDocument, 'get_locale')
        def test_document_get_locale_success(self, mock_get_locale):
            mock_get_locale.return_value = b"C"
            self.assertEqual(self.info.document_get_locale(), u"C")

        @mock.patch.object(AtspiDocument, '_get_locale')
        def test_document_get_locale_gerror_fail(self, mock_get_locale):
            gerror = _GError()
            gerror.code = 222
            gerror.message = b"Mocked GError message"

            def stub_get_locale(atspi_doc_ptr, gerr_pp):
                self.assertEqual(type(atspi_doc_ptr), AtspiAccessible.get_document.restype)
                self.assertEqual(type(gerr_pp), (ctypes.POINTER(ctypes.POINTER(_GError))))
                gerr_pp[0] = ctypes.pointer(gerror)
                return b"C"

            mock_get_locale.side_effect = stub_get_locale

            expected_err_msg = "GError with code: {0}, message: '{1}'".format(
                               gerror.code, gerror.message.decode(encoding='UTF-8'))
            six.assertRaisesRegex(self,
                                  GErrorException,
                                  expected_err_msg,
                                  self.info.document_get_locale)

        @mock.patch.object(AtspiDocument, '_get_attribute_value')
        def test_document_get_attribute_value_success(self, mock_get_attribute_value):
            attrib = u"dummy attribute"
            mock_get_attribute_value.return_value = b"dummy val"
            self.assertEqual(self.info.document_get_attribute_value(attrib), u"dummy val")
            self.assertEqual(type(mock_get_attribute_value.call_args[0][1]), ctypes.c_char_p)

        @mock.patch.object(AtspiDocument, '_get_attributes')
        def test_document_get_attributes_success(self, mock_get_attributes):
            attrib = b"dummy attribute"
            mock_get_attributes.return_value = self._dic2ghash({attrib: b"dummy val"})
            res = self.info.document_get_attributes()
            self.assertEqual(len(res), 1)
            self.assertEqual(res[attrib.decode('utf-8')], u"dummy val")

        def _dic2ghash(self, d):
            """Utility function to create GLib ghash_table

            Limitations:
             - only for strings as key/value
             - to have valid pointers dictionary should consist of bytes
             - no GLib insertion/lookup operations after leaving the scope
               of the function, as hash/equal callbacks are released by GC
            """
            hash_cbk = _GStrHashFunc(lambda key: _g_str_hash(key))
            equal_cbk = _GStrEqualFunc(lambda v1, v2: _g_str_equal(v1, v2))

            ghash_table_p = _g_hash_table_new(hash_cbk, equal_cbk)
            for k, v in d.items():
                res = _g_hash_table_insert(ghash_table_p, k, v)
                if res == False:
                    raise ValueError("Failed to insert k='{0}', v='{1}'".format(k, v))

            return ghash_table_p

        def test_ghash2dic(self):
            """Test handling C-created ghash_table with string-based KV pairs"""
            ghash_table_p = self._dic2ghash({b"key1": b"val1", b"2key": b"value2"})

            dic = _ghash2dic(ghash_table_p)
            print(dic)
            self.assertEqual(len(dic), 2)
            self.assertEqual(dic[u"key1"], u"val1")
            self.assertEqual(dic[u"2key"], u"value2")


if __name__ == "__main__":
    unittest.main()
