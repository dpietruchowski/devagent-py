from tree_sitter import Parser, Query

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

    def _extract_code(self, node):
        return self.code[node.start_byte:node.end_byte].decode("utf-8")

    def _run_query(self, query_str, node=None):
        query = Query(self.parser.language, query_str)
        if node:
            return query.matches(node)
        return query.matches(self.root_node)
    
    def print_node_tree_lines(self, node=None, indent=0, max_code_len=30):
        if node is None:
            node = self.root_node

        prefix = "  " * indent
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        node_text = self.code[node.start_byte:node.end_byte].decode("utf-8").replace("\n", "\\n")
        if len(node_text) > max_code_len:
            node_text = node_text[:max_code_len] + "..."

        print(f"{prefix}{node.type} [line {start_line} - {end_line}]: '{node_text}'")

        for i, child in enumerate(node.children):
            field_name = node.field_name_for_child(i)
            if field_name:
                print(f"{prefix}  (field: {field_name})")
            self.print_node_tree_lines(child, indent + 2, max_code_len=max_code_len)

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
