from django.utils.cache import add_never_cache_headers


class NoCacheMiddleware:
    """
    Forces Cache-Control: no-store on all admin-prefixed URLs so that
    the browser back button never replays CRUD operation pages.
    Also applies no-cache headers to all authenticated user pages.
    """

    # URL prefixes that belong to the custom admin section
    ADMIN_PREFIXES = (
        '/admin-auth/',
        '/admin-category/',
        '/admin-product/',
        '/admin-orders/',
        '/admin_coupon/',
        '/admin-offers/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Always prevent caching on admin pages regardless of login state
        if any(request.path.startswith(prefix) for prefix in self.ADMIN_PREFIXES):
            add_never_cache_headers(response)
            # Belt-and-suspenders: set headers directly so no proxy/browser ignores them
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response

        # For all other authenticated pages, apply softer no-cache
        if hasattr(request, 'user') and request.user.is_authenticated:
            add_never_cache_headers(response)

        return response
