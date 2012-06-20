# TODO(apugachev) get rid of GentleException


class KeystoneExpiresException(Exception):
    pass


class GentleException(Exception):
    pass


class BillingAPIError(Exception):
    pass
