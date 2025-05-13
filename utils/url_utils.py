from urllib.parse import urlsplit, urljoin, quote, unquote, urlencode, parse_qs

def url_parse(url):
    """Remplace werkzeug.urls.url_parse"""
    return urlsplit(url)

def url_join(base, url, allow_fragments=True):
    """Remplace werkzeug.urls.url_join"""
    return urljoin(base, url, allow_fragments=allow_fragments)

def url_quote(string, charset='utf-8', safe='/:', errors=None):
    """Remplace werkzeug.urls.url_quote"""
    return quote(string, safe=safe, encoding=charset, errors=errors)

def url_encode(obj, charset='utf-8', sort=False, key=None, separator='&'):
    """Remplace werkzeug.urls.url_encode"""
    if sort:
        obj = dict(sorted(obj.items(), key=key))
    return urlencode(obj, doseq=True)

def url_decode(qs, charset='utf-8', decode_keys=False, include_empty=True, errors='replace', separator='&'):
    """Remplace werkzeug.urls.url_decode"""
    return parse_qs(qs, keep_blank_values=include_empty, encoding=charset, errors=errors) 