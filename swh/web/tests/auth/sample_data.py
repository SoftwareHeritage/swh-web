# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


realm_public_key = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnqF4xvGjaI54P6WtJvyGayxP8A93u"
    "NcA3TH6jitwmyAalj8dN8/NzK9vrdlSA3Ibvp/XQujPSOP7a35YiYFscEJnogTXQpE/FhZrUY"
    "y21U6ezruVUv4z/ER1cYLb+q5ZI86nXSTNCAbH+lw7rQjlvcJ9KvgHEeA5ALXJ1r55zUmNvuy"
    "5o6ke1G3fXbNSXwF4qlWAzo1o7Ms8qNrNyOG8FPx24dvm9xMH7/08IPvh9KUqlnP8h6olpxHr"
    "drX/q4E+Nzj8Tr8p7Z5CimInls40QuOTIhs6C2SwFHUgQgXl9hB9umiZJlwYEpDv0/LO2zYie"
    "Hl5Lv7Iig4FOIXIVCaDGQIDAQAB"
)

oidc_profile = {
    "access_token": (
        # decoded token:
        # {'acr': '1',
        #  'allowed-origins': ['*'],
        #  'aud': ['swh-web', 'account'],
        #  'auth_time': 1592395601,
        #  'azp': 'swh-web',
        #  'email': 'john.doe@example.com',
        #  'email_verified': False,
        #  'exp': 1592396202,
        #  'family_name': 'Doe',
        #  'given_name': 'John',
        #  'groups': ['/staff'],
        #  'iat': 1582723101,
        #  'iss': 'http://localhost:8080/auth/realms/SoftwareHeritage',
        #  'jti': '31fc50b7-bbe5-4f51-91ef-8e3eec51331e',
        #  'name': 'John Doe',
        #  'nbf': 0,
        #  'preferred_username': 'johndoe',
        #  'realm_access': {'roles': ['offline_access', 'uma_authorization']},
        #  'resource_access': {'account': {'roles': ['manage-account',
        #                                            'manage-account-links',
        #                                            'view-profile']}},
        #  'scope': 'openid email profile',
        #  'session_state': 'd82b90d1-0a94-4e74-ad66-dd95341c7b6d',
        #  'sub': 'feacd344-b468-4a65-a236-14f61e6b7200',
        #  'typ': 'Bearer'
        #  }
        "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJPSnhV"
        "Q0p0TmJQT0NOUGFNNmc3ZU1zY2pqTXhoem9vNGxZaFhsa1c2TWhBIn0."
        "eyJqdGkiOiIzMWZjNTBiNy1iYmU1LTRmNTEtOTFlZi04ZTNlZWM1MTMz"
        "MWUiLCJleHAiOjE1ODI3MjM3MDEsIm5iZiI6MCwiaWF0IjoxNTgyNzIz"
        "MTAxLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvYXV0aC9yZWFs"
        "bXMvU29mdHdhcmVIZXJpdGFnZSIsImF1ZCI6WyJzd2gtd2ViIiwiYWNj"
        "b3VudCJdLCJzdWIiOiJmZWFjZDM0NC1iNDY4LTRhNjUtYTIzNi0xNGY2"
        "MWU2YjcyMDAiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJzd2gtd2ViIiwi"
        "YXV0aF90aW1lIjoxNTgyNzIzMTAwLCJzZXNzaW9uX3N0YXRlIjoiZDgy"
        "YjkwZDEtMGE5NC00ZTc0LWFkNjYtZGQ5NTM0MWM3YjZkIiwiYWNyIjoi"
        "MSIsImFsbG93ZWQtb3JpZ2lucyI6WyIqIl0sInJlYWxtX2FjY2VzcyI6"
        "eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0"
        "aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xl"
        "cyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtz"
        "Iiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwg"
        "cHJvZmlsZSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Ikpv"
        "aG4gRG9lIiwiZ3JvdXBzIjpbXSwicHJlZmVycmVkX3VzZXJuYW1lIjoi"
        "am9obmRvZSIsImdpdmVuX25hbWUiOiJKb2huIiwiZmFtaWx5X25hbWUi"
        "OiJEb2UiLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIn0.neJ-"
        "Pmd87J6Gt0fzDqmXFeoy34Iqb5vNNEEgIKqtqg3moaVkbXrO_9R37DJB"
        "AgdFv0owVONK3GbqPOEICePgG6RFtri999DetNE-O5sB4fwmHPWcHPlO"
        "kcPLbVJqu6zWo-2AzlfAy5bCNvj_wzs2tjFjLeHcRgR1a1WY3uTp5EWc"
        "HITCWQZzZWFGZTZCTlGkpdyJTqxGBdSHRB4NlIVGpYSTBsBsxttFEetl"
        "rpcNd4-5AteFprIr9hn9VasIIF8WdFdtC2e8xGMJW5Q0M3G3Iu-LLNmE"
        "oTIDqtbJ7OrIcGBIwsc3seCV3eCG6kOYwz5w-f8DeOpwcDX58yYPmapJ"
        "6A"
    ),
    "expires_in": 600,
    "id_token": (
        "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJPSnhVQ0p0"
        "TmJQT0NOUGFNNmc3ZU1zY2pqTXhoem9vNGxZaFhsa1c2TWhBIn0.eyJqdGki"
        "OiI0NDRlYzU1My1iYzhiLTQ2YjYtOTlmYS0zOTc3YTJhZDY1ZmEiLCJleHAi"
        "OjE1ODI3MjM3MDEsIm5iZiI6MCwiaWF0IjoxNTgyNzIzMTAxLCJpc3MiOiJo"
        "dHRwOi8vbG9jYWxob3N0OjgwODAvYXV0aC9yZWFsbXMvU29mdHdhcmVIZXJp"
        "dGFnZSIsImF1ZCI6InN3aC13ZWIiLCJzdWIiOiJmZWFjZDM0NC1iNDY4LTRh"
        "NjUtYTIzNi0xNGY2MWU2YjcyMDAiLCJ0eXAiOiJJRCIsImF6cCI6InN3aC13"
        "ZWIiLCJhdXRoX3RpbWUiOjE1ODI3MjMxMDAsInNlc3Npb25fc3RhdGUiOiJk"
        "ODJiOTBkMS0wYTk0LTRlNzQtYWQ2Ni1kZDk1MzQxYzdiNmQiLCJhY3IiOiIx"
        "IiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJuYW1lIjoiSm9obiBEb2UiLCJn"
        "cm91cHMiOltdLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJqb2huZG9lIiwiZ2l2"
        "ZW5fbmFtZSI6IkpvaG4iLCJmYW1pbHlfbmFtZSI6IkRvZSIsImVtYWlsIjoi"
        "am9obi5kb2VAZXhhbXBsZS5jb20ifQ.YB7bxlz_wgLJSkylVjmqedxQgEMee"
        "JOdi9CFHXV4F3ZWsEZ52CGuJXsozkX2oXvgU06MzzLNEK8ojgrPSNzjRkutL"
        "aaLq_YUzv4iV8fmKUS_aEyiYZbfoBe3Y4dwv2FoPEPCt96iTwpzM5fg_oYw_"
        "PHCq-Yl5SulT1nTrJZpntkf0hRjmxlDO06JMp0aZ8xS8RYJqH48xCRf_DARE"
        "0jJV2-UuzOWI6xBATwFfP44kV6wFmErLN5txMgwZzCSB2OCe5Cl1il0eTQTN"
        "ybeSYZeZE61QtuTRUHeP1D1qSbJGy5g_S67SdTkS-hQFvfrrD84qGflIEqnX"
        "ZbYnitD1Typ6Q"
    ),
    "not-before-policy": 0,
    "refresh_expires_in": 1800,
    "refresh_token": (
        "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJmNjM"
        "zMDE5MS01YTU4LTQxMDAtOGIzYS00ZDdlM2U1NjA3MTgifQ.eyJqdGk"
        "iOiIxYWI5ZWZmMS0xZWZlLTQ3MDMtOGQ2YS03Nzg1NWUwYzQyYTYiLC"
        "JleHAiOjE1ODI3MjQ5MDEsIm5iZiI6MCwiaWF0IjoxNTgyNzIzMTAxL"
        "CJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvYXV0aC9yZWFsbXMv"
        "U29mdHdhcmVIZXJpdGFnZSIsImF1ZCI6Imh0dHA6Ly9sb2NhbGhvc3Q"
        "6ODA4MC9hdXRoL3JlYWxtcy9Tb2Z0d2FyZUhlcml0YWdlIiwic3ViIj"
        "oiZmVhY2QzNDQtYjQ2OC00YTY1LWEyMzYtMTRmNjFlNmI3MjAwIiwid"
        "HlwIjoiUmVmcmVzaCIsImF6cCI6InN3aC13ZWIiLCJhdXRoX3RpbWUi"
        "OjAsInNlc3Npb25fc3RhdGUiOiJkODJiOTBkMS0wYTk0LTRlNzQtYWQ"
        "2Ni1kZDk1MzQxYzdiNmQiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOl"
        "sib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwic"
        "mVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFu"
        "YWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXc"
        "tcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbG"
        "UifQ.xQYrl2CMP_GQ_TFqhsTz-rTs3WuZz5I37toi1eSsDMI"
    ),
    "scope": "openid email profile",
    "session_state": "d82b90d1-0a94-4e74-ad66-dd95341c7b6d",
    "token_type": "bearer",
}

userinfo = {
    "email": "john.doe@example.com",
    "email_verified": False,
    "family_name": "Doe",
    "given_name": "John",
    "groups": ["/staff"],
    "name": "John Doe",
    "preferred_username": "johndoe",
    "sub": "feacd344-b468-4a65-a236-14f61e6b7200",
}
