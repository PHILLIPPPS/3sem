import unittest
from tool import lexer, parse, evaluate_expression

class TestConfigLanguage(unittest.TestCase):
    def test_constants(self):
        tokens = lexer("name: 'example'")
        config = parse(tokens)
        self.assertEqual(config, {'name': 'example'})

    def test_arrays(self):
        tokens = lexer("items: << 'apple', 'banana', 'cherry' >>")
        config = parse(tokens)
        self.assertEqual(config, {'items': ['apple', 'banana', 'cherry']})

    def test_expression(self):
        expr = ['10', '5', '+']
        result = evaluate_expression(expr, {})
        self.assertEqual(result, 15)

    def test_nested_arrays(self):
        tokens = lexer("nested: << <<1, 2>>, <<3, 4>> >>")
        config = parse(tokens)
        self.assertEqual(config, {'nested': [[1, 2], [3, 4]]})

if __name__ == '__main__':
    unittest.main()
