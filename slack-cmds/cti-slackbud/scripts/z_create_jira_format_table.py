"""
 Script to create a JIRA table fromat, from a cut-n-paste with known column witdh.
 Note... converting \n in |  mod column width
"""


def convert_iam_user_eol_text_to_jira_table_format(raw_text, num_columns):
    """
    Do a cut-and-paste of the users from IAM console, but need to  convert into a JIRA table.
    :param raw_text: The raw cut-and-paste from AWS console, IAM Users tab.
    :param num_columns: Number of columns in the AWS console table.
    :return:
    """
    lines = raw_text.split('\n')
    ret_val = ''

    curr_row = 1
    curr_col = 0

    # Cut and paste from IAM User table needs to combine access column.
    is_combine_access_items_mode = False
    combine_access_index = 0
    combine_access_items = []

    for curr_item in lines:
        if curr_item in 'Console access:' and not is_combine_access_items_mode:
            is_combine_access_items_mode = True
        if is_combine_access_items_mode:
            combine_access_items.append(curr_item)
            combine_access_index += 1
            if combine_access_index == 4:
                # finished combining text.
                combined_text = 'c: {}, k: {}'.format(combine_access_items[1], combine_access_items[3])
                print('____ combined_text = {}'.format(combined_text))
                ret_val += '|{}'.format(combined_text)
                curr_col += 1
                is_combine_access_items_mode = False
                combine_access_index = 0
                combine_access_items = []
        else:
            if curr_col < num_columns:
                ret_val += '|{}'.format(curr_item)
                curr_col += 1
            elif curr_item in 'Virtual' or curr_item in 'Not enabled':
                curr_row += 1
                curr_col = 0
                ret_val += '|{}|INACTIVATED_DATE|NOTE|\n'.format(curr_item)

        print('curr_row = {}, curr_col = {}, curr_item = {}, combine = {}'
              .format(curr_row, curr_col, curr_item, is_combine_access_items_mode))

    return ret_val


def get_raw_text_cti():
    """
    Paste text here.
    :return:
    """
    text = """aratnaparkhi
ReadOnly and NLU-RD
 374 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Not enabled
bataras-traefik
None
 409 days
None
Console access:
None
Programmatic access:
409 days
409 days
Not enabled
cpatil
AdminUSWest1
 900 days
158 days
Console access:
87 days
Programmatic access:
5 days
5 days
Virtual
ctipoke
ReadOnly
 None
None
None
Not enabled
gitlab-ee-es
None
 520 days
None
Console access:
None
Programmatic access:
372 days
372 days
Not enabled
interstella
ReadOnly
 1019 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
izaitsev-local-dev
AdminUSWest1
 655 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Not enabled
jecortez
AdminUSWest1
 950 days
950 days
Console access:
44 days
Programmatic access:
Yesterday
Yesterday
Virtual
jeroberts-dev
AdminUSWest1 and jeroberts-kops
 516 days
None
Console access:
None
Programmatic access:
Today
Today
Virtual
jeroberts-kops
jeroberts-kops
 444 days
None
Console access:
None
Programmatic access:
425 days
425 days
Not enabled
kvaggelakos
AdminUSWest1
 74 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Not enabled
leonid
Admins
 887 days
None
Console access:
None
Programmatic access:
8 days
8 days
Not enabled
pmangalath
AdminUSWest1
 438 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Not enabled
polly
tts2-access
 426 days
None
Console access:
None
Programmatic access:
201 days
201 days
Not enabled
qjiang
None
 480 days
None
Console access:
None
Programmatic access:
446 days
446 days
Not enabled
schristou
Admins
 662 days
None
Console access:
None
Programmatic access:
3 days
3 days
Not enabled
sergiy-local-dev
AdminUSWest1
 263 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Virtual
sriise
Admins
 1026 days
None
Console access:
None
Programmatic access:
25 days
25 days
Not enabled
trust-eng-keys-publisher
None
 766 days
None
Console access:
None
Programmatic access:
603 days
603 days
Not enabled
vborg
AdminUSWest1
 527 days
None
Console access:
None
Programmatic access:
337 days
337 days
Not enabled
vminyaylo-local-dev
AdminUSWest1
 407 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Not enabled
voice-client
None
 162 days
None
Console access:
None
Programmatic access:
115 days
115 days
Not enabled
whitney
None
 212 days
None
Console access:
None
Programmatic access:
191 days
191 days
Not enabled
yrybitskyi-local-dev
AdminUSWest1
 208 days
None
Console access:
None
Programmatic access:
Yesterday
Yesterday
Not enabled"""

    return text


def get_raw_text_neteng():
    """

    :return:
    """
    text="""arcadia-logrepo
AllowUsersMFA
 1777 days
None
Console access:
None
Programmatic access:
209 days
209 days
Not enabled
asnyder_for_sso
Admins
 16 days
16 days
Console access:
16 days
Programmatic access:
None
16 days
Not enabled
averma
Admins and AllowUsersMFA
 660 days
67 days
Console access:
65 days
Programmatic access:
640 days
65 days
Virtual
core-upload
None
 723 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
cores293741-read-only
cores-read-only and AllowUsersMFA
 2152 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
cvincelette
Admins
 227 days
139 days
Console access:
20 days
Programmatic access:
None
20 days
Virtual
dea-billing
None
 1013 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
deployrunner
None
 1203 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
firmware-sync
roku-plugins-dev , roku-plugins-qa , and 1 more
 1466 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
jscott
archiver , Admins , and 1 more
 2280 days
69 days
Console access:
2 days
Programmatic access:
Today
Today
Virtual
leonid
Admins and AllowUsersMFA
 1157 days
138 days
Console access:
13 days
Programmatic access:
244 days
13 days
Virtual
lphillips
AllowUsersMFA
 None
None
Console access:
579 days
Programmatic access:
None
579 days
Not enabled
pwu
AllowUsersMFA
 None
178 days
Console access:
25 days
Programmatic access:
None
25 days
Virtual
roku-content-mgr
roku-content-mgrs and AllowUsersMFA
 1761 days
None
Console access:
None
Programmatic access:
578 days
578 days
Not enabled
roku-eng-backup-user
S3BackupUsers and AllowUsersMFA
 2467 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
roku-log-repo
roku-log-repo , archiver , and 1 more
 2159 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
sriise
Admins and AllowUsersMFA
 None
58 days
Console access:
5 days
Programmatic access:
None
5 days
Virtual
todds
roku-log-data , roku-log-repo-ro , and 2 more
 1965 days
859 days
Console access:
808 days
Programmatic access:
3 days
3 days
Virtual
vtroyanker
AllowUsersMFA , roku-plugins-dev , and 2 more
 1515 days
None
Console access:
1515 days
Programmatic access:
2 days
2 days
Not enabled"""

    return text


def get_raw_text_web():
    """

    :return:
    """
    text = """aagashe
WebDev , DevOps , and 1 more
 278 days
486 days
Console access:
59 days
Programmatic access:
Today
Today
Virtual
redacted@email.com
Logs and AppsTeam
 None
171 days
Console access:
94 days
Programmatic access:
None
94 days
Virtual
redacted@email.com
Logs and TrustEngTeam
 None
186 days
Console access:
185 days
Programmatic access:
None
185 days
Virtual
acui
WebDev and WebEngTeam
 1034 days
319 days
Console access:
3 days
Programmatic access:
18 days
3 days
Virtual
adave
WebDev and WebEngTeam
 355 days
348 days
Console access:
20 days
Programmatic access:
None
20 days
Virtual
adazzi
WebDev and CloudInfraTeam
 467 days
466 days
Console access:
438 days
Programmatic access:
None
438 days
Virtual
api-blog-engineering-ghost
API
 1220 days
None
Console access:
None
Programmatic access:
39 days
39 days
Not enabled
api-blog-engineering-ghost-ses
API
 1217 days
None
Console access:
None
Programmatic access:
1217 days
1217 days
Not enabled
api-developer-transaction-user
API
 1119 days
None
Console access:
None
Programmatic access:
44 days
44 days
Not enabled
Aseella
WebDev and WebEngTeam
 628 days
628 days
Console access:
32 days
Programmatic access:
Today
Today
Virtual
redacted@email.com
ContentTooling , Contractor , and 1 more
 38 days
None
Console access:
None
Programmatic access:
23 days
23 days
Not enabled
ashah
WebDev , DevOps , and 1 more
 486 days
486 days
Console access:
3 days
Programmatic access:
Today
Today
Virtual
asnyder@roku.com
DevOps and CTI
 None
145 days
Console access:
143 days
Programmatic access:
None
143 days
Virtual
redacted@email.com
Developer , Enterprise , and 1 more
 156 days
153 days
Console access:
3 days
Programmatic access:
3 days
3 days
Virtual
authProviderLdap
WebDev and API
 1329 days
None
Console access:
None
Programmatic access:
1122 days
1122 days
Not enabled
awagle
WebDev
 67 days
None
Console access:
None
Programmatic access:
4 days
4 days
Not enabled
awells
WebDev , DevOps , and 1 more
 485 days
165 days
Console access:
18 days
Programmatic access:
2 days
2 days
Virtual
beesformachineguns
Automation
 1546 days
None
Console access:
None
Programmatic access:
524 days
524 days
Not enabled
blog
WebDev
 1586 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
bphan
WebDev and WebEngTeam
 405 days
144 days
Console access:
66 days
Programmatic access:
2 days
2 days
Virtual
btriplett
PartnerMgt
 None
None
None
Not enabled
bwilliams
WebDev and AppsTeam
 654 days
530 days
Console access:
244 days
Programmatic access:
None
244 days
Virtual
redacted@email.com
OEM
 111 days
None
Console access:
114 days
Programmatic access:
None
114 days
Not enabled
cchan
WebDev , DevOps , and 1 more
 507 days
235 days
Console access:
90 days
Programmatic access:
Today
Today
Virtual
ckodali
WebDev , DevOps , and 1 more
 283 days
283 days
Console access:
55 days
Programmatic access:
2 days
2 days
Virtual
redacted@email.com
Logs and AppsTeam
 None
310 days
Console access:
310 days
Programmatic access:
None
310 days
Virtual
redacted@email.com
WebDev and CloudInfraTeam
 314 days
257 days
Console access:
118 days
Programmatic access:
5 days
5 days
Virtual
cvincelette
WebDev and DataTeam
 None
1074 days
Console access:
17 days
Programmatic access:
633 days
17 days
Virtual
dea-developer
WebDev and DataTeam
 691 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
dea-gdpr
API
 425 days
None
None
Not enabled
DShatila
Logs
 433 days
304 days
Console access:
215 days
Programmatic access:
None
215 days
Virtual
dspitzer
WebDev and OEM
 843 days
843 days
Console access:
202 days
Programmatic access:
Today
Today
Virtual
EBProductionVPCAdmin
Admin
 None
489 days
None
Not enabled
eco
API
 1584 days
None
None
Not enabled
email-service
API
 1459 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
experiments-store
API
 1462 days
None
Console access:
None
Programmatic access:
1241 days
1241 days
Not enabled
eyu
WebDev and WebEngTeam
 278 days
1090 days
Console access:
24 days
Programmatic access:
24 days
24 days
Virtual
fkong
AppsTeam
 1195 days
1201 days
Console access:
475 days
Programmatic access:
563 days
475 days
Virtual
redacted@email.com
WebDev
 352 days
326 days
Console access:
11 days
Programmatic access:
27 days
11 days
Virtual
redacted@email.com
WebDev and AppsTeam
 457 days
341 days
Console access:
18 days
Programmatic access:
3 days
3 days
Virtual
fye
WebDev and WebEngTeam
 25 days
None
Console access:
None
Programmatic access:
2 days
2 days
Not enabled
gitlab
None
 1529 days
None
Console access:
None
Programmatic access:
3 days
3 days
Not enabled
global-logic-dev-tools
Contractor , DevTools , and 1 more
 384 days
None
Console access:
None
Programmatic access:
2 days
2 days
Not enabled
global-logic-web-content
Contractor and API
 118 days
None
Console access:
None
Programmatic access:
4 days
4 days
Not enabled
redacted@email.com
Logs
 318 days
321 days
Console access:
317 days
Programmatic access:
None
317 days
Virtual
htonthat
OEM
 472 days
472 days
Console access:
442 days
Programmatic access:
68 days
68 days
Virtual
redacted@email.com
WebDev and AppsTeam
 37 days
None
Console access:
None
Programmatic access:
12 days
12 days
Not enabled
iorizu
WebDev and WebEngTeam
 746 days
284 days
Console access:
26 days
Programmatic access:
2 days
2 days
Virtual
ipan
OEM
 458 days
433 days
Console access:
206 days
Programmatic access:
82 days
82 days
Virtual
jbraverman
PartnerMgt
 None
None
None
Not enabled
jecarter
WebDev and DataTeam
 None
216 days
Console access:
110 days
Programmatic access:
None
110 days
Virtual
redacted@email.com
WebDev , TrustEngTeam , and 1 more
 18 days
None
Console access:
None
Programmatic access:
2 days
2 days
Not enabled
jmerklin
WebDev and WebEngTeam
 284 days
284 days
Console access:
5 days
Programmatic access:
2 days
2 days
Virtual
jpearson
WebDev
 223 days
223 days
Console access:
40 days
Programmatic access:
None
40 days
Virtual
jroberts
WebDev , DevOps , and 1 more
 348 days
282 days
Console access:
95 days
Programmatic access:
32 days
32 days
Virtual
kagarwal
WebDev and DataTeam
 None
447 days
Console access:
121 days
Programmatic access:
None
121 days
Virtual
kitchensink
API
 None
None
None
Not enabled
ksandvick
PartnerMgt
 None
None
None
Not enabled
ksteele
WebDev , DevOps , and 1 more
 276 days
132 days
Console access:
45 days
Programmatic access:
2 days
2 days
Virtual
mchow
WebDev , DevOps , and 1 more
 128 days
283 days
Console access:
66 days
Programmatic access:
Today
Today
Virtual
redacted@email.com
Logs
 None
324 days
Console access:
307 days
Programmatic access:
None
307 days
Virtual
redacted@email.com
WebDev and DataTeam
 80 days
None
Console access:
None
Programmatic access:
44 days
44 days
Not enabled
mtaylor
WebDev and AppsTeam
 653 days
None
Console access:
None
Programmatic access:
303 days
303 days
Not enabled
newrelics
WebDev and API
 1682 days
None
None
Not enabled
redacted@email.com
AppsTeam and WebDev
 194 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
nvellanki
WebDev and WebEngTeam
 433 days
282 days
Console access:
23 days
Programmatic access:
2 days
2 days
Virtual
oem-portal-system-user
OEM , API , and 1 more
 208 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
pagerduty
API
 1292 days
None
Console access:
None
Programmatic access:
1292 days
1292 days
Not enabled
pBuiQuang
WebDev , DevOps , and 1 more
 282 days
279 days
Console access:
2 days
Programmatic access:
2 days
2 days
Virtual
pickle
None
 None
None
Console access:
None
Programmatic access:
388 days
388 days
Not enabled
redacted@email.com
Logs and AppsTeam
 None
310 days
Console access:
297 days
Programmatic access:
None
297 days
Virtual
pkim
Admin , WebDev , and 2 more
 None
142 days
Console access:
117 days
Programmatic access:
None
117 days
Virtual
prengasamy
WebDev and WebEngTeam
 706 days
683 days
Console access:
81 days
Programmatic access:
227 days
81 days
Virtual
psarkar
AppsTeam and Logs
 None
408 days
Console access:
72 days
Programmatic access:
None
72 days
Virtual
qjiang
WebDev and DevOps
 639 days
384 days
Console access:
3 days
Programmatic access:
3 days
3 days
Virtual
raugusto
WebDev , DevOps , and 1 more
 146 days
146 days
Console access:
12 days
Programmatic access:
2 days
2 days
Virtual
rburdick
WebDev
 1153 days
None
Console access:
979 days
Programmatic access:
4 days
4 days
Not enabled
rclode
WebDev
 32 days
None
Console access:
None
Programmatic access:
2 days
2 days
Not enabled
rkarnati
WebDev , DevOps , and 1 more
 282 days
118 days
Console access:
52 days
Programmatic access:
None
52 days
Virtual
redacted@email.com
Contractor , ContentTooling , and 1 more
 38 days
None
Console access:
None
Programmatic access:
23 days
23 days
Not enabled
rmahmoodi
WebDev , DevOps , and 1 more
 509 days
486 days
Console access:
27 days
Programmatic access:
4 days
4 days
Virtual
redacted@email.com
WebDev and TrustEngTeam
 None
164 days
Console access:
164 days
Programmatic access:
None
164 days
Virtual
roku_test
API
 None
None
None
Not enabled
roku-testrails
API
 1443 days
None
None
Not enabled
rpenn
WebDev and WebEngTeam
 368 days
283 days
Console access:
30 days
Programmatic access:
4 days
4 days
Virtual
rpm-s3-users
API
 1447 days
None
None
Not enabled
redacted@email.com
OEM and WebDev
 208 days
208 days
Console access:
3 days
Programmatic access:
2 days
2 days
Virtual
rtorchia
OEM
 473 days
433 days
Console access:
10 days
Programmatic access:
431 days
10 days
Virtual
rw-automation
Automation and WebDev
 556 days
None
Console access:
None
Programmatic access:
10 days
10 days
Not enabled
sarbaugh
OEM
 474 days
474 days
Console access:
206 days
Programmatic access:
339 days
206 days
Virtual
schristou
WebDev
 80 days
555 days
Console access:
27 days
Programmatic access:
73 days
27 days
Virtual
seppalapally
WebDev and AppsTeam
 1173 days
1066 days
Console access:
3 days
Programmatic access:
2 days
2 days
Virtual
ses-smtp-roku-forum.20160516-145746
API
 1140 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
ses-smtp-user.20150413-150050
API
 1539 days
None
Console access:
None
Programmatic access:
5 days
5 days
Not enabled
ses-smtp-user.20160229-184252
API
 1217 days
None
None
Not enabled
ses-smtp-user.20161216-155601
API
 926 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
ses-smtp-user.20161216-164736
API and SES
 926 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
ses-smtp-user.20170419-145454
API
 802 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
ses-smtp-user.20170605-140134
API
 755 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
ses-smtp-user.radioroku
API
 846 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
sgurusamy
WebDev and AppsTeam
 None
566 days
Console access:
333 days
Programmatic access:
None
333 days
Virtual
skeng
WebDev , DevOps , and 2 more
 261 days
284 days
Console access:
9 days
Programmatic access:
2 days
2 days
Virtual
smtp-ossec-user
None
 1558 days
None
Console access:
None
Programmatic access:
10 days
10 days
Not enabled
sriise
WebDev and CloudInfraTeam
 None
1069 days
Console access:
210 days
Programmatic access:
881 days
210 days
Virtual
sshin
PartnerMgt
 None
None
None
Not enabled
ssrinivas
WebDev , DevOps , and 1 more
 146 days
284 days
Console access:
13 days
Programmatic access:
2 days
2 days
Virtual
test1
Contractor and API
 356 days
None
Console access:
None
Programmatic access:
349 days
349 days
Not enabled
TestWebEng
WebDev and API
 1455 days
None
Console access:
None
Programmatic access:
340 days
340 days
Not enabled
tschwartz
DevOps , WebDev , and 1 more
 283 days
283 days
Console access:
48 days
Programmatic access:
2 days
2 days
Virtual
vbalas
WebDev
 174 days
173 days
Console access:
41 days
Programmatic access:
Today
Today
Virtual
redacted@email.com
OEM and WebDev
 394 days
None
Console access:
395 days
Programmatic access:
3 days
3 days
Not enabled
redacted@email.com
DevOps , WebDev , and 1 more
 486 days
486 days
Console access:
81 days
Programmatic access:
2 days
2 days
Virtual
redacted@email.com
WebDev
 341 days
341 days
Console access:
11 days
Programmatic access:
3 days
3 days
Virtual
redacted@email.com
WebDev
 None
374 days
Console access:
2 days
Programmatic access:
None
2 days
Virtual
redacted@email.com
WebDev and Enterprise
 68 days
None
None
Not enabled"""

    return text

def get_raw_text_apps_qa():
    """

    :return:
    """
    text = """aavella
Admin-Users
 655 days
366 days
Console access:
212 days
Programmatic access:
14 days
14 days
Virtual
absharma
Admin-Users and Admins
 173 days
298 days
Console access:
18 days
Programmatic access:
173 days
18 days
Virtual
akornilov
Admin-Users
 None
500 days
Console access:
194 days
Programmatic access:
None
194 days
Virtual
amandybura
Admin-Users
 404 days
374 days
Console access:
3 days
Programmatic access:
3 days
3 days
Virtual
aseetharaman
Admin-Users
 None
265 days
Console access:
263 days
Programmatic access:
None
263 days
Virtual
baas-test-user
test_dynamo_rds_s3_full_access
 516 days
None
Console access:
None
Programmatic access:
513 days
513 days
Not enabled
bgoswami
Admin-Users
 None
717 days
Console access:
135 days
Programmatic access:
None
135 days
Virtual
bwilliams
Admin-Users
 None
731 days
Console access:
571 days
Programmatic access:
None
571 days
Virtual
channelstore-installs
S3-Full-Access
 1409 days
None
Console access:
None
Programmatic access:
971 days
971 days
Not enabled
crobertson
Admins
 3 days
656 days
Console access:
249 days
Programmatic access:
2 days
2 days
Virtual
csa
Admins
 None
None
Console access:
None
Programmatic access:
1144 days
1144 days
Not enabled
dbns_user
None
 481 days
None
Console access:
None
Programmatic access:
477 days
477 days
Not enabled
deployer
Admins
 1034 days
None
Console access:
None
Programmatic access:
62 days
62 days
Not enabled
dynaconf-test-user
None
 808 days
None
Console access:
None
Programmatic access:
131 days
131 days
Not enabled
e1qa-components-test
S3-Full-Access
 566 days
None
Console access:
None
Programmatic access:
6 days
6 days
Not enabled
EmailTemplateLibraryUser
TestUsers and Admins
 796 days
None
Console access:
None
Programmatic access:
530 days
530 days
Not enabled
es-aws
None
 1048 days
None
Console access:
None
Programmatic access:
1024 days
1024 days
Not enabled
fkong
Admin-Users and Admins
 1019 days
1328 days
Console access:
577 days
Programmatic access:
2 days
2 days
Virtual
fsmith
Admin-Users
 None
395 days
Console access:
395 days
Programmatic access:
None
395 days
Virtual
gradle_commons_test_user
S3-Full-Access
 774 days
None
Console access:
None
Programmatic access:
248 days
248 days
Not enabled
ihassan
test_dynamo_rds_s3_full_access
 105 days
None
None
Not enabled
ikrimer
Admin-Users
 872 days
1032 days
Console access:
152 days
Programmatic access:
24 days
24 days
Virtual
indus-test-user
None
 541 days
None
Console access:
None
Programmatic access:
523 days
523 days
Not enabled
interstella
None
 1227 days
None
Console access:
1227 days
Programmatic access:
Today
Today
Not enabled
jcooper
Admin-Users
 None
452 days
Console access:
222 days
Programmatic access:
222 days
222 days
Virtual"""

    return text


def get_raw_text_jump():
    """

    :return:
    """
    text = """aavella
RokuPay
 None
200 days
Console access:
27 days
Programmatic access:
None
27 days
Virtual
adas
Devs
 607 days
27 days
Console access:
Today
Programmatic access:
2 days
Today
Virtual
adazzi
CTI
 516 days
202 days
Console access:
95 days
Programmatic access:
3 days
3 days
Virtual
ailangovan
Devs
 514 days
167 days
Console access:
4 days
Programmatic access:
2 days
2 days
Virtual
amajumdar
Devs
 657 days
125 days
Console access:
4 days
Programmatic access:
46 days
4 days
Virtual
amalhotra
Devs
 461 days
41 days
Console access:
2 days
Programmatic access:
2 days
2 days
Virtual
anarayanan
RokuPay
 146 days
200 days
Console access:
79 days
Programmatic access:
39 days
39 days
Virtual
areynolds
Devs and Apps-Admins
 228 days
52 days
Console access:
12 days
Programmatic access:
5 days
5 days
Virtual
asnyder
Devs and Admins
 None
12 days
Console access:
12 days
Programmatic access:
None
12 days
Virtual
bataras
CTI
 507 days
157 days
Console access:
10 days
Programmatic access:
2 days
2 days
Virtual
bhsiao
Apps-Devs
 242 days
62 days
Console access:
5 days
Programmatic access:
None
5 days
Virtual
bnoffsinger
Devs
 1021 days
174 days
Console access:
6 days
Programmatic access:
2 days
2 days
Virtual
chammond
Devs
 597 days
52 days
Console access:
18 days
Programmatic access:
26 days
18 days
Virtual
ckoz
Apps-Devs
 249 days
65 days
Console access:
Yesterday
Programmatic access:
None
Yesterday
Virtual
crobertson
Devs and Apps-Admins
 289 days
118 days
Console access:
3 days
Programmatic access:
2 days
2 days
Virtual
cyeh
Firmware_BAR
 508 days
160 days
Console access:
101 days
Programmatic access:
30 days
30 days
Virtual
dlin
Devs
 1215 days
135 days
Console access:
19 days
Programmatic access:
2 days
2 days
Virtual
dqi
Devs
 159 days
233 days
Console access:
53 days
Programmatic access:
2 days
2 days
Virtual
dspitzer
Lonestar
 369 days
205 days
Console access:
30 days
Programmatic access:
2 days
2 days
Virtual
ehaughin
Firmware_BAR
 438 days
256 days
Console access:
100 days
Programmatic access:
2 days
2 days
Virtual
fbartosh
Devs
 646 days
96 days
Console access:
17 days
Programmatic access:
3 days
3 days
Virtual
fkong
SelfManaged and Apps-Admins
 335 days
5 days
Console access:
2 days
Programmatic access:
Today
Today
Virtual
fsmith
Apps-Devs
 207 days
18 days
Console access:
18 days
Programmatic access:
None
18 days
Virtual
gcuni
Devs
 1209 days
82 days
Console access:
12 days
Programmatic access:
20 days
12 days
Virtual
gpires
Devs
 936 days
45 days
Console access:
3 days
Programmatic access:
2 days
2 days
Virtual
gsundaram
Apps-Devs
 249 days
69 days
Console access:
11 days
Programmatic access:
4 days
4 days
Virtual
htorbasinovic
Devs
 733 days
26 days
Console access:
12 days
Programmatic access:
3 days
3 days
Virtual
ihassan
Apps-Devs
 194 days
15 days
Console access:
3 days
Programmatic access:
3 days
3 days
Virtual
ikrimer
RokuPay
 207 days
207 days
Console access:
41 days
Programmatic access:
None
41 days
Virtual
interstella
None
 1214 days
None
Console access:
None
Programmatic access:
Today
Today
Not enabled
izaitsev
CTI
 None
118 days
Console access:
3 days
Programmatic access:
None
3 days
Virtual
jcooper
Apps-Devs
 11 days
25 days
Console access:
2 days
Programmatic access:
3 days
2 days
Virtual
jeroberts
CTI
 None
165 days
Console access:
2 days
Programmatic access:
None
2 days
Virtual
jhausler
Apps-Devs
 244 days
40 days
Console access:
25 days
Programmatic access:
None
25 days
Virtual
jpatel
QA
 646 days
104 days
Console access:
2 days
Programmatic access:
2 days
2 days
Virtual
jstipins
Devs
 243 days
17 days
Console access:
17 days
Programmatic access:
None
17 days
Virtual
jswaminathan
Devs
 691 days
185 days
Console access:
16 days
Programmatic access:
6 days
6 days
Virtual
jxu
RokuPay
 None
200 days
Console access:
41 days
Programmatic access:
None
41 days
Virtual
kchu
Apps-Devs
 249 days
76 days
Console access:
6 days
Programmatic access:
None
6 days
Virtual
kman
RokuPay
 207 days
24 days
Console access:
4 days
Programmatic access:
None
4 days
Virtual
knguyen
QA
 990 days
130 days
Console access:
3 days
Programmatic access:
Today
Today
Virtual
kshah
Apps-Devs
 95 days
95 days
Console access:
Today
Programmatic access:
3 days
Today
Virtual
kvaggelakos
CTI
 340 days
167 days
Console access:
3 days
Programmatic access:
55 days
3 days
Virtual
lliu
Devs
 194 days
19 days
Console access:
3 days
Programmatic access:
Today
Today
Virtual
mdespotovic
Devs
 899 days
58 days
Console access:
16 days
Programmatic access:
369 days
16 days
Virtual
mgupta
Apps-Devs
 249 days
68 days
Console access:
5 days
Programmatic access:
None
5 days
Virtual
mnigudkar
RokuPay
 None
19 days
Console access:
3 days
Programmatic access:
None
3 days
Virtual
mnimmagadda
Devs
 935 days
82 days
Console access:
4 days
Programmatic access:
Today
Today
Virtual
mtaylor
Apps-Devs
 207 days
18 days
Console access:
12 days
Programmatic access:
None
12 days
Virtual
mugupta
Devs
 419 days
54 days
Console access:
2 days
Programmatic access:
2 days
2 days
Virtual
myeremin
Apps-Devs
 244 days
62 days
Console access:
10 days
Programmatic access:
None
10 days
Virtual
naggarwal
Devs
 249 days
79 days
Console access:
10 days
Programmatic access:
4 days
4 days
Virtual
nbuckner
RokuPay
 146 days
19 days
Console access:
5 days
Programmatic access:
19 days
5 days
Virtual
njain
Apps-Devs
 73 days
73 days
Console access:
10 days
Programmatic access:
None
10 days
Virtual
npatel
QA
 971 days
146 days
Console access:
13 days
Programmatic access:
3 days
3 days
Virtual
ogofman
Devs
 46 days
27 days
Console access:
17 days
Programmatic access:
None
17 days
Virtual
pbagrecha
Devs
 754 days
27 days
Console access:
4 days
Programmatic access:
4 days
4 days
Virtual
pcaire
Devs
 115 days
115 days
Console access:
25 days
Programmatic access:
Today
Today
Virtual
pkasireddy
Apps-Devs
 None
194 days
Console access:
48 days
Programmatic access:
None
48 days
Virtual
pmangalath
CTI
 438 days
74 days
Console access:
3 days
Programmatic access:
438 days
3 days
Virtual
pmishra
Apps-Devs
 249 days
82 days
Console access:
41 days
Programmatic access:
172 days
41 days
Virtual
pvlasenko
Devs
 268 days
90 days
Console access:
74 days
Programmatic access:
2 days
2 days
Virtual
qzhong
Devs and Apps-Admins
 706 days
158 days
Console access:
2 days
Programmatic access:
2 days
2 days
Virtual
rbeam
Apps-Devs
 244 days
73 days
Console access:
41 days
Programmatic access:
32 days
32 days
Virtual
rdhandapani
Apps-Devs
 156 days
73 days
Console access:
Today
Programmatic access:
26 days
Today
Virtual
rgundimeda
Apps-Devs
 207 days
39 days
Console access:
4 days
Programmatic access:
4 days
4 days
Virtual
rjethwa
Devs
 472 days
54 days
Console access:
45 days
Programmatic access:
Yesterday
Yesterday
Virtual
rkuzyk
Devs
 54 days
26 days
Console access:
26 days
Programmatic access:
4 days
4 days
Virtual
rmirizzi
Devs
 1215 days
146 days
Console access:
13 days
Programmatic access:
Today
Today
Virtual
rmittapalli
RokuPay
 207 days
33 days
Console access:
4 days
Programmatic access:
None
4 days
Virtual
rramaseshan
Apps-Devs
 178 days
178 days
Console access:
11 days
Programmatic access:
36 days
11 days
Virtual
rray
Devs
 69 days
67 days
Console access:
61 days
Programmatic access:
Yesterday
Yesterday
Virtual
rseetharama
RokuPay
 23 days
173 days
Console access:
13 days
Programmatic access:
12 days
12 days
Virtual
schristou
CTI and Admins
 None
102 days
Console access:
11 days
Programmatic access:
None
11 days
Virtual
sgirolkar
QA
 1152 days
132 days
Console access:
5 days
Programmatic access:
2 days
2 days
Virtual
sgurusamy
Apps-Devs
 249 days
81 days
Console access:
6 days
Programmatic access:
None
6 days
Virtual
skiran
Devs
 251 days
83 days
Console access:
5 days
Programmatic access:
5 days
5 days
Virtual
smazurenko
Devs
 44 days
46 days
Console access:
6 days
Programmatic access:
4 days
4 days
Virtual
ssamant
Apps-Devs
 66 days
72 days
Console access:
Today
Programmatic access:
65 days
Today
Virtual
ssaraiya
Devs
 509 days
145 days
Console access:
17 days
Programmatic access:
Today
Today
Virtual
standon
Apps-Devs
 124 days
81 days
Console access:
3 days
Programmatic access:
117 days
3 days
Virtual
swalia
Apps-Devs
 194 days
194 days
Console access:
17 days
Programmatic access:
None
17 days
Virtual
syavorsky
CTI
 None
142 days
Console access:
5 days
Programmatic access:
None
5 days
Virtual
tkurack
SelfManaged
 None
37 days
Console access:
11 days
Programmatic access:
None
11 days
Virtual
twan
Apps-Devs
 150 days
79 days
Console access:
4 days
Programmatic access:
2 days
2 days
Virtual
varjunan
Apps-Devs
 103 days
68 days
Console access:
44 days
Programmatic access:
2 days
2 days
Virtual
vinguyen
Devs
 440 days
90 days
Console access:
3 days
Programmatic access:
2 days
2 days
Virtual
vminyaylo
CTI
 408 days
122 days
Console access:
2 days
Programmatic access:
408 days
2 days
Virtual
vpathi
Apps-Devs and Apps-Admins
 289 days
104 days
Console access:
2 days
Programmatic access:
None
2 days
Virtual
vsubramanian
Apps-Devs
 207 days
25 days
Console access:
3 days
Programmatic access:
206 days
3 days
Virtual
ypolishchuk
GlobalLogic and Devs
 209 days
39 days
Console access:
2 days
Programmatic access:
40 days
2 days
Virtual
yrybitskyi
CTI
 209 days
31 days
Console access:
11 days
Programmatic access:
209 days
11 days
Virtual
zhwang
Devs
 277 days
61 days
Console access:
13 days
Programmatic access:
2 days
2 days
Virtual
zwang
Devs
 472 days
109 days
Console access:
4 days
Programmatic access:
3 days
3 days
Virtual"""

    return text


if __name__ == '__main__':
    #  from AWS CodeBuild during build stage
    try:
        # raw_text = get_raw_text_cti()
        # raw_text = get_raw_text_neteng()
        # raw_text = get_raw_text_web()
        # raw_text = get_raw_text_apps_qa()
        raw_text = get_raw_text_jump()
        jira_table = convert_iam_user_eol_text_to_jira_table_format(raw_text, 6)
        print('\n----------\n')
        print(jira_table)
    except Exception as ex:
        print('Exception: {}'.format(ex))
