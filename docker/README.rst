Docker deployment of the Revrit API
===================================

There are two containers needed for the Revrit API (normally called
the ``arcapi`` in code, since _Revrit_ is a newer name).

1. The web server (the arcapi container)
2. The Solr index (the ubuntu-solr container)

arcapi
------
This container hosts the Python application. At the moment, it serves
directly with with the Tornado web server and doesn't sit behind a
proxy. Tornado is designed to serve thousands of simultaneous
connections and is often used without a proxy. However, a proxy can be
added if it becomes necessary. There is no SSL for the arcapi at the
moment, but it can be added with a few lines of code. Inside of the
container, it serves on port 8888 because it does not run as root, but
this can be mapped to anything on the outside.

The container also has a small read-only SQLite database and some data
files present on the build machine, but not in the git repository.

All the actual application code installed from git repositories with
``pip`` at build-time and installed in a virtual environment.

One thing to be aware of is that this web server spawns multiple
worker process inside the container to handle the computationally
intensive work so it can continue to take connections.

ubuntu-solr
-----------
This container sets up a fresh Solr install. The Solr data itself
lives in a volume, though this isn't strictly necessary because it is
more or less read-only once the database is constructed. However, it
is about 1GB, and it seemed reasonable not to include it in the image
itself.

However, this complicates the build process, as the index now has to
be constructed in the running container. For the moment, this can be
done without issue on the host machine, but ultimately Solr's port
should not be open to the public, obviously.

I am aware there is talk about setting up a Solr cloud instance, and
eventually my cores should be moved there, rather than having their
own container and volume.
