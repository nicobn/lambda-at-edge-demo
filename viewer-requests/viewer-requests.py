import re

HEADER = 'x-rule-matches'

RULES = {
    "RULE_C1": '^/c/[0-9]{3}/?$',
    "RULE_C2": '^/c/(.*)$',
    "RULE_C3": '^/c/?$',
    "RULE_D1": '^/d/[0-9]{3}/?$',
    "RULE_D2": '^/d/(.*)$',
    "RULE_D3": '^/d/?$',
}

def handler(event, context):
    request = event['Records'][0]['cf']['request']
    uri = request['uri']

    ruleMatch = 'NONE'
    for ruleName, ruleExpression in RULES.items():
        matches = re.search(ruleExpression, uri)

        if matches:
            ruleMatch = ruleName
            break

    request['headers'][HEADER] = [{
        "key": HEADER,
        "value": ruleMatch
    }]

    return request