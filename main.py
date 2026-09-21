# actual code only
print("chandan")
print("hfdtge")

'''
# daily push file in github
git add .
git commit -m "comment""
git push -u origin main
'''

import langgraph
import langgraph.checkpoint.sqlite

print("LangGraph version:", getattr(langgraph, "__version__", "unknown"))
print("SQLite checkpoint module:", langgraph.checkpoint.sqlite)