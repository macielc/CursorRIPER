content = open('run_smoke_test_hibrido.py', 'r', encoding='utf-8').read()
content = content.replace("refined_config['parameters']", "refined_config['param_grid']")
content = content.replace("config['parameters']", "config['param_grid']")
open('run_smoke_test_hibrido.py', 'w', encoding='utf-8').write(content)
print("Fixed!")

