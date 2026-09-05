import sys
sys.path.insert(0, '.')
sys.path.insert(0, './backend')

import os
os.chdir('./backend')

exec(open('test_parashari_yogas_phase5b.py').read())