import aws_util
# import roku_token_fetcher


def get_jwt_token():
    """
    A valid token is cached in SSM Parameter store.
    pull it from there, check the expiration time, and
    refresh if needed.
    :return:
    """
    return aws_util.get_ssm_parameter("slack_bud_jwt_token")


def add_jwt_token_to_headers(headers):
    """

    :param headers:
    :return:
    """
    token = get_jwt_token()
    header_txt = 'Bearer {}'.format(token)
    headers['Authorization'] = header_txt

    return headers


# MOVE this code into a different lambda function to avoid too many
#      code dependenies in SlackBud.
#
# def fetch_new_jwt_token():
#     """
#     Create a new JWT token and store it in Parameter Store.
#     :return:
#     """
#     new_jwt_token = roku_token_fetcher.fetch('cti-common',
#                                              'https://ss.cti.asnyder.com:8443',
#                                              'secret/cti/jwt/common')
#
#     # Need a put_ssm_parameter command.
#     print(" ------ start JWT Token -------- \n{}\n ------  end  JWT Token -------- \n".format(new_jwt_token))