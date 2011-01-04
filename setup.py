from distutils.core import setup
import os, sys

path, script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(path))

setup(name='devpayments-tornado',
      version='1.4.3',
      description='/dev/payments tornado python bindings',
      author='Greplin',
      author_email='daniel@greplin.com',
      url='http://www.greplin.com/',
      packages=['devpayments'],
      package_dir = {'devpayments' : 'src'}
)

