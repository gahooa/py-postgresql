##
# copyright 2009, James William Pye
# http://python.projects.postgresql.org
##
r"""
`postgresql.driver`
===================

The `postgresql.driver` implements PG-API, `postgresql.api`, using PQ version
3.0 to connect to PostgreSQL servers. It makes use of the protocol's extended
features to provide binary datatype transmission and protocol level prepared
statements.

Compatibility
-------------

The project currently supports PostgreSQL servers as far back as 8.0. Prior
versions are not tested. While any version of PostgreSQL supporting version 3.0
of the PQ protocol *should* work, some of the higher level features will not
work due to the lack of supporting stored procedures.

Conventions
-----------

In most examples, the ``db`` identifier to used to reference the connection
object.

Connecting
==========

Connecting to PostgreSQL using `postgresql.driver` is very simple::

	>>> import postgresql.driver as pg_driver
	>>> db = pg_driver.connect(user = 'usename', password = 'secret', host = 'localhost', port = 5432)

NOTE: `connect` will *not* inherit parameters from the environment as
libpq-based drivers do.

Connection Keywords
-------------------

 ``user``
  The user to connect as.
 ``password``
  The user's password.
 ``database``
  The name of the database to connect to. (PostgreSQL defaults it to `user`)
 ``host``
  The hostname or IP address to connect to.
 ``port``
  The port on the host to connect to.
 ``settings``
  A dictionary or key-value pair sequence stating the parameters to give to the
  database. These settings are included in the startup packet, and should be
  used carefully as if a setting is invalid it will cause the connection to fail.

 ``connect_timeout``
  Amount of time to wait for a connection to be made. (in seconds)
  Raises `postgresql.exceptions.ConnectionTimeoutError` when triggered.
 ``server_encoding``
  Hint given to the driver to properly encode password data and some information
  in the startup packet.
  This should only be used in cases where connections cannot be made due to
  authentication failures that occur while using known-correct credentials.

 ``sslmode``
  ``'disable'``
   Don't allow SSL connections.
  ``'allow'``
   Try without SSL, but if that doesn't work, try with.
  ``'prefer'``
   Try SSL first, then without.
  ``'require'``
   Require an SSL connection.

 ``sslcrtfile``
  Certificate file path given to `ssl.wrap_socket`.
 ``sslkeyfile``
  Key file path given to `ssl.wrap_socket`.
 ``sslrootcrtfile``
  Root certificate file path given to `ssl.wrap_socket`
 ``sslrootcrlfile``
  Revocation list file path. [Currently not checked.]

Connection Metadata
-------------------

When a connection is established, certain pieces of metadata are collected from
the backend. The following are the attributes set on the connection object after
the connection is made:

 ``version``
  The results of ``SELECT version()``
 ``version_info``
  A ``sys.version_info`` form of the ``server_version`` setting. eg. ``(8, 1, 2,
  'final', 0)``.
 ``backend_id``
  The process-id of the backend process.
 ``backend_start``
  When backend was started. ``datetime.datetime`` instance.
 ``client_address``
  The client address that the backend is communicating with.
 ``client_port``
  The port of the client that the backend is communicating with.
 ``security``
  `None` if no security. ``'ssl'`` if SSL is enabled.

The latter three are collected from pg_stat_activity. If this information is
unavailable, the attributes will be `None`.

Database Interface Entry Points
-------------------------------

After a connection is established, the interface entry points are ready for use.
These entry points are the primary interfaces used to create prepared statements
or stored procedure references. These entry points exists as attributes on the
connection object:

 ``prepare(sql_statement_string)``
  Create a `postgresql.api.PreparedStatement` object for querying the database.
  See `Prepared Statement` for more information.

 ``execute(sql_statements_string)``
  Run a block of SQL on the server. This method returns `None` unless an error
  occurs. If errors occur, the first error will be raised.

 ``statement_from_id(statement_id)``
  Create a `postgresql.api.PreparedStatement` object from an existing statement
  identifier. This is used in cases where the statement was prepared on the
  server.

 ``cursor_from_id(cursor_id)``
  Create a `postgresql.api.Cursor` object from an existing cursor identifier.
  This is used in cases where the cursor was declared on the server, but use was
  desired by the client.

 ``proc(procedure_id)``
  Create a `postgresql.api.StoredProcedure` object referring to a stored
  procedure on the database. The returned object will provide a
  `collections.Callable` interface to the stored procedure on the server.

 ``xact``
  The `postgresql.api.TransactionManager` instance for managing the connection's
  transactions. See `Transaction Management` for more information.

 ``settings``
  A `collections.MutableMapping` interface to the database's SQL settings. See
  `Settings Management` for more information.

Client Parameters
-----------------

Connection creation interfaces in `postgresql.driver` are purposefully simple.
All parameters are keywords, and are taken literally. libpq-based drivers
tend differ as they inherit defaults client parameters from the environment.
Doing this by default is undesirable as it can cause suspicious failures due to
unexpected parameter inheritance. Of course, using these parameters in many
cases is simply expected. The `postgresql.clientparameters` module provides a
means to collect them into one dictionary-object for subsequent application to
a connection entry point.

The primary entry points are `postgresql.clientparameters` is

 `postgresql.clientparameters.standard`: Build a client parameter dictionary
 from the environment and parsed command line options.

  ``co``
   Options parsed by `postgresql.clientparameters.StandardParser` or
   `postgresql.clientparameters.DefaultParser`.
  ``no_defaults``
   Don't include defaults like ``pgpassfile`` and ``user``.
  ``environ``
   Environment to extract client parameter variables from. Defaults to
   `os.environ`.
  ``environ_prefix``
   Environment variable prefix to use. Defaults to "PG".
  ``default_pg_sysconfdir``
   The location of the pg_service.conf file. ``PGSYSCONFDIR`` environment
   overrides this.
  ``pg_service_file``
   Explicit location of the service file. Overrides "sysconfdir" based path.
  ``prompt_title``
   Descriptive title to use if a password prompt is needed. `None` to disable
	password resolution--disables pgpassfile lookups.
  ``parameters``
   Base client parameters to use. These are layered on top of the defaults(The
	defaults that can be disabled by ``no_defaults``).

 `postgresql.clientparameters.resolve_password`: Resolve the password for the
 given client parameters dictionary returned by ``standard``. By default, this
 function is unnecessary as ``standard`` will resolve the password by default.
 However, it may be desirable to run this if password resolution is disabled by
 passing ``standard``'s ``prompt_title`` keyword argument as `None`.

  ``parameters``
   First positional argument. Normalized client parameters dictionary to update
	in-place with the resolved password. If the 'prompt_password' key is in
	``parameters``, it will prompt regardless(normally comes from ``-W``).
  ``getpass``
   Function to call to prompt for the password. Defaults to `getpass.getpass`.
  ``prompt_title``
   Additional title to use if a prompt is requested. This can also be specified
	in the ``parameters`` as the ``prompt_title`` key.

Example usage::

	import postgresql.clientparameters as pg_param
	p = pg_param.DefaultParser()
	co, ca = p.parse_args(...)
	cp = pg_param.standard(co = co)
	print(cp)

The `postgresql.clientparameters` module is executable, so you can see the
results of the above snippet by::

	$ python -m postgresql.clientparameters -h localhost -U a_db_user -ssearch_path=public
	{'host': 'localhost',
	 'password': None,
	 'port': 5432,
	 'settings': {'search_path': 'public'},
	 'user': 'a_db_user'}

Connectors
----------

Connectors are the supporting objects used to instantiate a connection. They
exist for the purpose of providing connections with the necessary abstractions
for facilitating the client's communication with the server, and to act as a
container for the client parameters. The latter purpose is of primary interest
to this section.

Each connection object is associated with its connector by the ``connector``
attribute on the connection. This provides the user with access to the
parameters used to establish the connection in the first place. The attributes
on the connector should *not* be altered. If parameters changes are needed, a
new connector should be created.

The attributes available on a connector are consistent with the names of the
connection parameters described in `Connection Keywords`, so that list can be
used as a reference for the available information.

Prepared Statements
===================

Prepared statements are the primary entry point for initiating an operation on
the database. Prepared statement objects represent a request that will, likely,
be sent to the database at some point in the future.

A statement is a single SQL command.

Querying
--------

Querying PostgreSQL is very easy. A statement object is created, a
`postgresql.api.PreparedStatement` instance, using the `prepare` method on the
connection object::

	>>> my_statement = db.prepare("SELECT 'hello, world!'")

This creates a bound statement object, so it's only usable on the `db`
connection. While this may seem to be a trifle for some situations, it's very
handy to be able to pass around the statement object without having to explicitly
carry the connection object with it.

Now, to execute it::

	>>> my_results = my_statement()

Just like executing a function. In this case, invoking `my_statement` will return a
`Cursor` object to the result set.

NOTE: Don't confuse PG-API cursors with DB-API cursors. PG-API cursors are SQL
cursors and don't contain methods for executing more queries within the cursor;
rather, they only hold the results 

Cursor objects have a few ways to rows out of them:

 ``next(my_results)`` (``my_results.__next__``)
  This fetches the next row in the cursor object. Cursors support the iterator
  protocol, you can just as easily:

 ``for nextrow in my_results:``
  This will, of course, get the ``nextrow`` in the cursor, ``my_results``, until
  the cursor is exhausted. This and the former way of reading rows use the same
  method, ``__next__``, per the `collections.Iterator` API.

 ``my_results.read(5)``
  This method name is borrowed from `file` objects, and are semantically
  similar. However, this being a cursor, rows are returned instead of bytes or
  characters. In this case, five rows are requested, but certainly only one will
  come back: ``[('hello, world!',)]``. When the number of rows returned is less
  then the number requested, it means that cursor has been exhausted, and there
  are no more rows to be read.

 ``my_results.chunks``
  This access point is designed for situations where rows are being moved
  quickly. It is a property that provides an ``collections.Iterator`` that returns
  *sequences* of rows. The size of the "chunks" produced is *normally* consistent
  with the ``chunksize`` attribute on the cursor object itself. This is the
  fastest way to move rows.

As cursors have a couple methods for reading tuples, queries a few methods for
executing the prepared statement:

 ``__call__(...)``
  As shown before, statement objects can be simply invoked like a function to get a
  cursor to the statement's results.

 ``first(...)``
  For simple queries, a cursor object can be a bit tiresome to get data from,
  consider the data contained in ``my_results``, 'hello world!'. To get at this
  data directly from the ``__call__(...)`` method, it looks something like::

	>>> my_statement().read()[0][0]

  While it's certainly easy to understand, it can be quite cumbersome and
  perhaps even error prone for more complicated queries returing single values.

  To simplify access to simple data, the ``first`` method will simply return
  the "first" of the result set.

  The first value
   When there is a single row with a single column, ``first()`` will return
   the contents of that cell.

  The first row
   When there is a single row with multiple columns, ``first()`` will return
   that row.

  The first column
   When there is a single column with multiple rows, ``first()`` will return
   that column as a sequence.

  The first row count
   When DML--for instance, an INSERT-statement--is executed, ``first()`` will
   return the row count returned by the statement as an integer.

  The result set created by the statement determines what is actually returned.
  Naturally, a statement used with ``first()`` should be crafted with these
  rules in mind.

Statement objects can take parameters. To do this, the statement must be defined using
PostgreSQL's positional parameter notation. ``$1``, ``$2``, ``$3``, etc. If the
statement object ``my_statement`` were to be re-written to take a parameter, it would be
done simply::

	>>> my_statement = db.prepare("SELECT $1")

And, re-create the ``my_cursor``::

	>>> my_cursor = my_statement('hello, world!')

It's that easy. And using ``first()``::

	>>> 'hello, world!' == my_statement.first('hello, world!')
	True

Inserting and DML
-----------------

Loading data into the database is just as easy as getting data out. Again,
prepared statements are used to facilitate the exchange. In these examples, a
table definition is necessary complete the illustration::

	>>> db.execute(
	... 	'''
	... CREATE TABLE employee (
	... 	employee_name text,
	... 	employee_salary numeric,
	... 	employee_dob date,
	... 	employee_hire_date data
	... );
	... 	'''
	... )

Prepare the statement object:

	>>> mk_employee = db.prepare("INSERT INTO employee VALUES ($1, $2, $3, $4)")

And add "Mr. Johnson" to the table:

	>>> import datetime
	>>> dmlr = mk_employee(
	... 	"John Johnson",
	... 	"92,000",
	... 	datetime.date(1950, 12, 10),
	... 	datetime.date(1998, 4, 23)
	... )
	>>> print(dmlr.command())
	INSERT
	>>> print(dmlr.count())
	1

The execution of DML will return a utility cursor. Utility cursors are fully
completed prior to returning control to the user.

Scrollable Cursors
------------------

By default, cursors are not scrollable. It is assumed, for performance reasons,
that the user just wants the contents in a linear fashion. However, scrollable
cursors are supported. To create a scrollable cursor, call the statement with
the ``with_scroll`` keyword argument set to `True`.

The cursor interface supports scrolling using the ``seek`` method. Like
``read``, it is semantically similar to a file's ``seek()``. ``seek`` takes two
arguments: ``position`` and ``whence``:

 ``position``
  The position to scroll to. The meaning of this is determined by ``whence``.

 ``whence``
  How to use the position: absolute, relative, or absolute from end:

   absolute: ``'ABSOLUTE'`` or ``0`` (default)
    seek to the absolute position in the cursor relative to the beginning of the
    cursor.

	relative: ``'RELATIVE'`` or ``1``
    seek to the relative position. 

   from end: ``'FROM_END'`` or ``2``
    seek to the absolute position relative from the end of the cursor.

COPY
----

`postgresql.driver` transparently supports PostgreSQL's COPY command. To the
user, it will act exactly like a cursor that produces tuples with the only
recommendation being that the cursor *should* be completed before other
actions take place on the connection.

In situations where other actions are invoked during a ``COPY TO STDOUT``, the
entire result set of the COPY will be read. However, no error will be raised so
long as there is enough memory available, so it is quite desirable to avoid
doing other actions on the connection while a COPY is active.

In situations where other actions are invoked during a ``COPY FROM STDIN``, a
COPY failure error will be thrown by the database. The driver manages the
connection state in such a way that will purposefully cause the error as the
COPY was inappropriately interrupted. This not usually a problem as the
``load(...)`` method must complete the COPY before returning.

Copy data is always transferred using ``bytes`` objects. Even in cases where the
COPY is not in ``BINARY`` mode. The user is expected to perform any
necessary encoding translations on the COPY data sent or received from the
database. This is done to avoid any unnecessary overhead by default.

``COPY FROM STDIN`` commands are supported via
`postgresql.api.PreparedStatement.load`. Each invocation to ``load``
is a single invocation of COPY. ``load`` takes an iterable of COPY lines
to send to the server::

	CREATE TABLE sample_copy (
		sc_number int,
		sc_text text
	);
	>>> copyin = db.prepare('COPY sample_copy FROM STDIN')
	>>> copyin.load([
	... 	b'123\tone twenty three\n',
	... 	b'350\ttree fitty\n',
	... ])

Copy cursors and the load interface was designed to be used together so that
direct transfers from a source database to a destination database could be made:

	>>> copyout = src.prepare('COPY atable TO STDOUT')
	>>> copyin = dst.prepare('COPY atable FROM STDIN')
	>>> copyin.load(copyout())

However, for non-threaded applications, this doesn't provide any means for status
updates to be provided to the user, so the preferred method would be to make use
of the ``chunks`` iterator on the copy cursor:

	>>> with dst.xact:
	... 	for ck in copyout().chunks:
	... 		copyin.load(ck)
	... 		update_process_status(len(ck))

This will execute the ``COPY ... FROM STDIN`` statement multiple times, but
with the transaction block on the "dst"(destination) database, it will be all or
nothing.

Transaction Management
======================

To simplify transaction management, an interface extension is provided on the
``xact`` attribute of connection objects. This extension provides interfaces for
managing the transaction state of the database. It provides the necessary
interfaces for starting, committing, and aborting transactions and,
transparently, savepoints.

The attributes available on ``xact``:

 ``start(...)``
  Start a transaction block, or set a savepoint if already in a transaction
  block. The savepoint identifier is automatically generated based on the
  transaction "depth".

 ``depth``
  The "depth" of the transaction state. This is incremented every time the
  ``start()`` method is called. If the depth is greater than `1`, it means that
  the database is in a savepoint.

 ``commit()``
  Commit the transaction block or release the savepoint.

 ``abort()``
  Abort the transaction block or rollback to the savepoint associated with the
  current depth.

 ``failed``
  A property indicating one of three states:

   `False`
    In an active transaction-block.

   `True`
    In a failed transaction-block. Savepoints can make this `False` again
	 without reaching zero-depth.

   `None`
    Not in a transaction block. (``start()`` hasn't been called)

With the introduction of with-statements, Python introduced a mechanism
that allows for the provision of a convenient syntax for transaction
management. It's a very obvious application of with-statements and documentation
is near-unnecessary::

	>>> with db.xact:
	... 	...

And savepoints are completely abstracted as well::

	>>> with db.xact:
	... 	with db.xact:
	... 		...
	... 	with db.xact:
	... 		...

The first time a transaction is started, it will open a transaction block using
``START TRANSACTION``. Subsequently, further transaction entries create a
savepoint whose name corresponds to the ``depth``.

**Using the with-statement syntax for managing transactions is strongly
recommended.**

HINT: "Zero-depth" means no active transaction block. It's the default
"transaction depth" when a connection is establish. It's normally referred to
when the transaction state has ascended to the ceiling.

Transaction Configuration
-------------------------

In order to specify the isolation level, some configuration is necessary.
The ``xact`` property on a connection is callable; this interface
uses the keywords passed into the invocation for establishing the configuration:

	>>> with db.xact(isolation = 'serializeable'):
	... 	...

The actual string given as the isolation level is given to the database.

Read-only is also supported:

	>>> with db.xact(readonly = True):
	... 	...

Savepoints transactions have no configuration--the identifiers are
automatically generated based on the transaction depth.

Prepared Transactions - Two Phase Commit
----------------------------------------

PostgreSQL's two-phase commit is supported by the `gid` keyword given to the
transaction's configuration:

	>>> with db.xact(gid = 'global identifier'):
	... 	...

If the ``commit()`` bringing the transaction to zero-depth sees a configured
`gid`, it will cause the transaction manager to issue a ``PREPARE TRANSACTION``
statement instead of a commit. Of course, provided that ``failed`` is `False`,
in which case the usual ``ABORT`` will be issued.

The global identifier can be configured at any time during the transaction, but
it is *strongly* recommended to specify it within the first transaction context
to enjoy clarity.

Settings Management
===================

SQL's SHOW and SET provides a means to configure runtime parameters on the
database("GUC"s). In order to save the user some grief, a
`collections.MutableMapping` interface is provided to simplify configuration.
This is especially useful for things settings like "search_path".

The ``settings`` attribute on the connection provides the interface extension. 

The standard dictionary interface is supported:

	>>> db.settings['search_path'] = "$user,public"

And ``update(...)`` is better performing:

	>>> db.settings.update({
	... 	'search_path' : "$user,public",
	... 	'default_statistics_target' : "1000"
	... })


"""

__docformat__ = 'reStructuredText'
if __name__ == '__main__':
	import sys
	if (sys.argv + [None])[1] == 'dump':
		sys.stdout.write(__doc__)
	else:
		try:
			help(__package__ + '.driver')
		except NameError:
			help(__name__)