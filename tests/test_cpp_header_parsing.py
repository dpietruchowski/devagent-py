import tempfile
import os

from lib.code_manager.editors.cpp_editor import CppFileEditor

def test_header_class_detection():
    code = """
    #ifndef MYCLASS_H
    #define MYCLASS_H

    #include <QObject>

    class MyClass : public QObject {
        Q_OBJECT
        Q_PROPERTY(int value READ value WRITE setValue NOTIFY valueChanged)

    public:
        MyClass();

        int value() const;
        void setValue(int val);

        static int staticCounter;

    private:
        int m_value;
    };

    #endif // MYCLASS_H
    """

    with tempfile.NamedTemporaryFile(suffix=".h", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        f.flush()

        editor = CppFileEditor()
        editor.load(f.name)

        classes = editor.get_handlers_list(category="classes")
        assert any(c.name == "MyClass" for c in classes), "Should detect MyClass"

        methods = editor.get_handlers_list(category="methods")
        method_names = [m.name for m in methods]
        assert "value" in method_names, "Should detect method 'value'"
        assert "setValue" in method_names, "Should detect method 'setValue'"
        # assert "MyClass" in method_names, "Should detect constructor 'MyClass'"

        properties = editor.get_handlers_list(category="properties", class_name="MyClass")
        prop_names = [p.name for p in properties if p.name]
        assert "value" in prop_names, "Should detect Q_PROPERTY 'value'"

        fields = editor.get_handlers_list(category="fields")
        field_names = [f.name for f in fields]
        assert "m_value" in field_names, "Should detect private field 'm_value'"
        assert "staticCounter" in field_names, "Should detect private field 'm_valstaticCounterue'"

    os.remove(f.name)
