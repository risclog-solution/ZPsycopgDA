# testutils.py - utility module for psycopg2 testing.

#
# Copyright (C) 2010-2011 Daniele Varrazzo  <daniele.varrazzo@gmail.com>
#
# psycopg2 is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# In addition, as a special exception, the copyright holders give
# permission to link this program with the OpenSSL library (or with
# modified versions of OpenSSL that use the same license as OpenSSL),
# and distribute linked combinations including the two.
#
# You must obey the GNU Lesser General Public License in all respects for
# all of the code used other than OpenSSL.
#
# psycopg2 is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.


# Use unittest2 if available. Otherwise mock a skip facility with warnings.

import sys

try:
    from functools import wraps
except ImportError:

    def wraps(orig):
        def wraps_(f):
            f.__name__ = orig.__name__
            return f

        return wraps_


try:
    import unittest2

    unittest = unittest2
except ImportError:
    import unittest

    unittest2 = None

if hasattr(unittest, "skipIf"):
    skip = unittest.skip
    skipIf = unittest.skipIf

else:
    import warnings

    def skipIf(cond, msg):
        def skipIf_(f):
            @wraps(f)
            def skipIf__(self):
                if cond:
                    warnings.warn(msg)
                    return
                else:
                    return f(self)

            return skipIf__

        return skipIf_

    def skip(msg):
        return skipIf(True, msg)

    def skipTest(self, msg):
        warnings.warn(msg)
        return

    unittest.TestCase.skipTest = skipTest

# Silence warnings caused by the stubborness of the Python unittest maintainers
# http://bugs.python.org/issue9424
if (
    not hasattr(unittest.TestCase, "assert_")
    or unittest.TestCase.assert_ is not unittest.TestCase.assertTrue
):
    # mavaff...
    unittest.TestCase.assert_ = unittest.TestCase.assertTrue
    unittest.TestCase.failUnless = unittest.TestCase.assertTrue
    unittest.TestCase.assertEquals = unittest.TestCase.assertEqual
    unittest.TestCase.failUnlessEqual = unittest.TestCase.assertEqual


def decorate_all_tests(cls, decorator):
    """Apply *decorator* to all the tests defined in the TestCase *cls*."""
    for n in dir(cls):
        if n.startswith("test"):
            setattr(cls, n, decorator(getattr(cls, n)))


def skip_before_postgres(*ver):
    """Skip a test on PostgreSQL before a certain version."""
    ver = ver + (0,) * (3 - len(ver))

    def skip_before_postgres_(f):
        @wraps(f)
        def skip_before_postgres__(self):
            if self.conn.server_version < int("%d%02d%02d" % ver):
                return self.skipTest(
                    "skipped because PostgreSQL %s" % self.conn.server_version
                )
            else:
                return f(self)

        return skip_before_postgres__

    return skip_before_postgres_


def skip_after_postgres(*ver):
    """Skip a test on PostgreSQL after (including) a certain version."""
    ver = ver + (0,) * (3 - len(ver))

    def skip_after_postgres_(f):
        @wraps(f)
        def skip_after_postgres__(self):
            if self.conn.server_version >= int("%d%02d%02d" % ver):
                return self.skipTest(
                    "skipped because PostgreSQL %s" % self.conn.server_version
                )
            else:
                return f(self)

        return skip_after_postgres__

    return skip_after_postgres_


def skip_before_python(*ver):
    """Skip a test on Python before a certain version."""

    def skip_before_python_(f):
        @wraps(f)
        def skip_before_python__(self):
            if sys.version_info[: len(ver)] < ver:
                return self.skipTest(
                    "skipped because Python %s"
                    % ".".join(map(str, sys.version_info[: len(ver)]))
                )
            else:
                return f(self)

        return skip_before_python__

    return skip_before_python_


def skip_from_python(*ver):
    """Skip a test on Python after (including) a certain version."""

    def skip_from_python_(f):
        @wraps(f)
        def skip_from_python__(self):
            if sys.version_info[: len(ver)] >= ver:
                return self.skipTest(
                    "skipped because Python %s"
                    % ".".join(map(str, sys.version_info[: len(ver)]))
                )
            else:
                return f(self)

        return skip_from_python__

    return skip_from_python_


def skip_if_no_superuser(f):
    """Skip a test if the database user running the test is not a superuser"""

    @wraps(f)
    def skip_if_no_superuser_(self):
        from psycopg2 import ProgrammingError

        try:
            return f(self)
        except ProgrammingError as e:
            import psycopg2.errorcodes

            if e.pgcode == psycopg2.errorcodes.INSUFFICIENT_PRIVILEGE:
                self.skipTest("skipped because not superuser")
            else:
                raise

    return skip_if_no_superuser_
