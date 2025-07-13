import os
import tempfile
import pytest

from lib.code_manager.editors.cpp_source_editor import CppSourceFileEditor

@pytest.fixture
def cpp_method_file():
    code = """
    #include <iostream>

    void MyClass::greet() {
        std::cout << "Greetings!" << std::endl;
    }

    int main() {
        MyClass obj;
        obj.greet();
        return 0;
    }
    """
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        f.flush()
        yield f.name
    os.remove(f.name)


def test_method_in_cpp_file_without_class_declaration(cpp_method_file):
    editor = CppSourceFileEditor()
    editor.load(cpp_method_file)

    methods = editor.get_handlers_list(category="methods", class_name="MyClass")
    assert len(methods) == 1, "Parser should find one method of class MyClass"

    method = methods[0]

    code_snippet = editor.get_code(method)
    assert code_snippet, "Code snippet should not be empty"
    assert "{" in code_snippet and "}" in code_snippet, "Code snippet should contain braces"
    assert "std::cout" in code_snippet
    assert "Greetings!" in code_snippet


def test_global_function_detection():
    code = """
    #include <iostream>

    void greet() {
        std::cout << "Hello!" << std::endl;
    }

    int main() {
        greet();
        return 0;
    }
    """
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        f.flush()
        editor = CppSourceFileEditor()
        editor.load(f.name)

        functions = editor.get_handlers_list(category="functions")
        assert len(functions) == 2, "Should detect two global functions (greet and main)"
        names = [func.name for func in functions]
        assert "greet" in names
        assert "main" in names

        for func in functions:
            code_snippet = editor.get_code(func)
            assert code_snippet, "Code snippet should not be empty"
            assert "{" in code_snippet and "}" in code_snippet, "Code snippet should contain braces"
            if func.name == "greet":
                assert "std::cout" in code_snippet, "greet function should contain std::cout"
            elif func.name == "main":
                assert "return 0;" in code_snippet, "main function should contain return 0;"

    os.remove(f.name)


def test_includes_detection():
    code = """
    #include <iostream>
    #include "myheader.h"

    int main() {
        return 0;
    }
    """
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        f.flush()
        editor = CppSourceFileEditor()
        editor.load(f.name)

        includes = editor.get_handlers_list(category="includes")
        assert len(includes) == 2, "Should detect two include directives"

        codes = [inc.get_code() for inc in includes]
        assert any("iostream" in code for code in codes), "Should find iostream include"
        assert any("myheader.h" in code for code in codes), "Should find myheader.h include"

    os.remove(f.name)


def test_global_vars_detection():
    code = """
    int global_var = 5;
    double pi = 3.14;

    int main() {
        return 0;
    }
    """
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        f.flush()
        editor = CppSourceFileEditor()
        editor.load(f.name)

        globals_ = editor.get_handlers_list(category="global_vars")
        names = [g.get_name() for g in globals_]
        assert "global_var" in names
        assert "pi" in names

        for g in globals_:
            code_snippet = editor.get_code(g)
            assert code_snippet, "Code snippet should not be empty"
            assert "=" in code_snippet, f"Code snippet for {g.get_name()} should contain initialization"
    os.remove(f.name)


def test_static_members_detection():
    code = """
    int MyClass::counter = 5;

    int main() {
        return MyClass::counter;
    }
    """
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        f.flush()
        editor = CppSourceFileEditor()
        editor.load(f.name)

        static_members = editor.get_handlers_list(category="static_members", class_name="MyClass")
        assert len(static_members) == 1, "Should detect one static member of MyClass"

        static_member = static_members[0]
        code_snippet = editor.get_code(static_member)
        assert code_snippet, "Code snippet for static member should not be empty"
        assert "counter" in code_snippet, "Static member code should contain variable name 'counter'"
        assert "= 5" in code_snippet or "5" in code_snippet, "Static member code should contain initialization to 5"

    os.remove(f.name)