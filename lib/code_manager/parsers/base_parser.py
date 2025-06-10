from tree_sitter import Parser, Query
import json, re

class BaseNodeHandler:
    def __init__(self, node, code):
        self.node = node
        self.code = code
        self.name = self._extract_name()

    def _extract_name(self):
        return None

    def get_code(self):
        return self.code[self.node.start_byte:self.node.end_byte].decode("utf-8")

    def get_start_line(self):
        return self.node.start_point[0] + 1

    def get_end_line(self):
        return self.node.end_point[0] + 1
    
class BaseParser:
    def __init__(self, language):
        self.parser = Parser(language)

    def parse(self, source_code: str):
        if isinstance(source_code, bytes):
            self.code = source_code
        else:
            self.code = source_code.encode("utf-8")
        self.tree = self.parser.parse(self.code)
        self.root_node = self.tree.root_node

        with open("full_tree_output.scm", "w", encoding="utf-8") as f:
            f.write(self.build_tree_string())


    def build_tree_string(self, node=None, indent=0, max_text_length=80):
        if node is None:
            node = self.root_node

        def _build(node, indent=0):
            raw_text = self.code[node.start_byte:node.end_byte].decode("utf8").strip()
            text = raw_text.replace("\n", " ").strip()
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."

            indent_str = "  " * indent
            line = f"{indent_str}({node.type} '{text}'"

            if not node.children:
                return line + ")\n"

            line += "\n"
            for i, child in enumerate(node.children):
                field_name = node.field_name_for_child(i)
                field_prefix = f"{field_name}: " if field_name else ""
                child_text = _build(child, indent + 1)
                # Insert field prefix after indentation
                child_text = child_text.replace("  " * (indent + 1), "  " * (indent + 1) + field_prefix, 1)
                line += child_text

            line += indent_str + ")\n"
            return line

        return _build(node)

    def _extract_code(self, node):
        return self.code[node.start_byte:node.end_byte].decode("utf-8")

    def _run_query(self, query_str, node=None):
        query = Query(self.parser.language, query_str)
        if node:
            return query.matches(node)
        return query.matches(self.root_node)

    def _extract_nodes(self, query, node=None, capture_keys=None):
        capture_keys = capture_keys or []
        matches = self._run_query(query, node)
        results = []
        for _, captures in matches:
            if all(key in captures for key in capture_keys):
                extracted = {key: captures[key] for key in capture_keys}
                results.append(extracted)
        return results

    def _get_handlers(self, query, capture_keys, handler_class, node=None, extra_args=None):
        extra_args = extra_args or {}
        results = []
        extracted_nodes_list = self._extract_nodes(query, node=node, capture_keys=capture_keys)
        for extracted_nodes in extracted_nodes_list:
            nodes_zip = zip(*(extracted_nodes[key] for key in capture_keys))
            for nodes_group in nodes_zip:
                kwargs = {}
                for key, node_value in zip(capture_keys, nodes_group):
                    kwargs[f"{key}"] = node_value
                kwargs.update(extra_args)
                handler = handler_class(**kwargs, code=self.code)
                results.append(handler)
        return results
