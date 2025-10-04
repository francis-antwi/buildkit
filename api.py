from buildkit.wsgi import application
from vercel_python.wsgi import RequestHandler

app = RequestHandler(application)