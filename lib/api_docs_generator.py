"""API Documentation Generator - Auto-generates API documentation from Flask routes."""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from flask import current_app
import inspect


class APIDocsGenerator:
    """Generate API documentation from Flask application routes."""
    
    AUTH_METHODS = {
        "require_admin": "Administrator role required",
        "require_login": "User login required",
        "require_user_permission": "User permission required",
        "csrf_protect": "CSRF token required",
    }
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.endpoints = []
    
    def generate_docs(self, app):
        """Generate complete API documentation from Flask app."""
        docs = {
            "timestamp": datetime.now().isoformat(),
            "title": "SiteForge API Documentation",
            "version": "1.0",
            "authentication": self._get_auth_methods(),
            "endpoints": [],
            "summary": {}
        }
        
        # Collect all routes from the app
        routes_by_blueprint = {}
        
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static':
                continue  # Skip static files
            
            endpoint = rule.endpoint
            blueprint = endpoint.split('.')[0] if '.' in endpoint else 'root'
            
            if blueprint not in routes_by_blueprint:
                routes_by_blueprint[blueprint] = []
            
            # Get the view function
            try:
                view_func = app.view_functions.get(endpoint)
            except:
                view_func = None
            
            route_info = {
                "path": str(rule),
                "methods": list(rule.methods - {'OPTIONS', 'HEAD'}),
                "endpoint": endpoint,
                "blueprint": blueprint,
                "description": self._extract_description(view_func),
                "auth": self._extract_auth_requirements(view_func),
                "parameters": self._extract_parameters(rule),
                "status_codes": self._extract_status_codes(view_func),
            }
            
            routes_by_blueprint[blueprint].append(route_info)
        
        # Build tree structure
        docs["endpoints"] = self._build_tree_structure(routes_by_blueprint)
        
        # Build summary statistics
        docs["summary"] = {
            "total_endpoints": sum(len(routes) for routes in routes_by_blueprint.values()),
            "total_blueprints": len(routes_by_blueprint),
            "blueprints": list(routes_by_blueprint.keys()),
            "methods_used": self._get_methods_summary(routes_by_blueprint),
        }
        
        return docs
    
    def _build_tree_structure(self, routes_by_blueprint):
        """Build hierarchical tree structure for API endpoints."""
        tree = {}
        
        for blueprint, routes in sorted(routes_by_blueprint.items()):
            blueprint_tree = {
                "name": blueprint,
                "routes": [],
                "count": len(routes),
                "methods": []
            }
            
            # Group routes by path prefix
            path_groups = {}
            method_set = set()
            for route in sorted(routes, key=lambda r: r['path']):
                # Get the main path prefix
                path_parts = route['path'].strip('/').split('/')
                prefix = path_parts[0] if path_parts else 'root'
                
                if prefix not in path_groups:
                    path_groups[prefix] = []
                
                path_groups[prefix].append(route)
                method_set.update(route['methods'])
            
            # Build nested structure
            for prefix in sorted(path_groups.keys()):
                prefix_group = {
                    "prefix": prefix,
                    "routes": path_groups[prefix]
                }
                blueprint_tree["routes"].append(prefix_group)
            
            blueprint_tree["methods"] = sorted(method_set)
            tree[blueprint] = blueprint_tree
        
        return tree
    
    def _extract_description(self, view_func):
        """Extract description from view function docstring."""
        if not view_func:
            return "No description available"
        
        if view_func.__doc__:
            # Get first line of docstring
            lines = view_func.__doc__.strip().split('\n')
            return lines[0] if lines else "No description available"
        
        return "No description available"
    
    def _extract_auth_requirements(self, view_func):
        """Extract authentication requirements from view function."""
        if not view_func:
            return []
        
        auth = []
        
        # Check for decorators in source code
        try:
            source = inspect.getsource(view_func)
            
            for auth_type, description in self.AUTH_METHODS.items():
                if f"@{auth_type}" in source or f".{auth_type}" in source:
                    auth.append({
                        "type": auth_type,
                        "description": description
                    })
        except:
            pass
        
        if not auth:
            auth.append({
                "type": "public",
                "description": "Public access"
            })
        
        return auth
    
    def _extract_parameters(self, rule):
        """Extract URL parameters from route rule."""
        params = []
        
        # Extract from URL pattern
        for arg in rule.arguments:
            params.append({
                "name": arg,
                "type": "string",
                "required": True,
                "location": "path"
            })
        
        return params
    
    def _extract_status_codes(self, view_func):
        """Extract possible status codes from view function."""
        status_codes = [
            {"code": 200, "description": "Success"}
        ]
        
        if not view_func:
            return status_codes
        
        try:
            source = inspect.getsource(view_func)
            
            # Look for abort or error handling
            if "abort(404)" in source or "404" in source:
                status_codes.append({"code": 404, "description": "Not found"})
            if "abort(403)" in source or "403" in source:
                status_codes.append({"code": 403, "description": "Forbidden"})
            if "abort(401)" in source or "401" in source:
                status_codes.append({"code": 401, "description": "Unauthorized"})
            if "abort(429)" in source or "429" in source or "rate" in source.lower():
                status_codes.append({"code": 429, "description": "Rate limited"})
        except:
            pass
        
        return status_codes
    
    def _get_auth_methods(self):
        """Return comprehensive authentication documentation."""
        return {
            "overview": "The SiteForge API supports multiple authentication methods.",
            "methods": [
                {
                    "type": "Session-based",
                    "description": "Traditional session cookies for browser-based access",
                    "usage": "Login via /auth/login endpoint, maintain session cookie",
                    "example": "POST /auth/login with credentials"
                },
                {
                    "type": "Administrator",
                    "description": "Endpoints requiring administrator privileges",
                    "usage": "User must have 'administrator' role",
                    "example": "Decorated with @auth.require_admin"
                },
                {
                    "type": "CSRF Protection",
                    "description": "CSRF tokens required for state-changing requests",
                    "usage": "Include _csrf_token in POST/PUT/DELETE requests",
                    "example": "Include hidden input with CSRF token"
                }
            ],
            "headers": {
                "Content-Type": "application/json or application/x-www-form-urlencoded",
                "Accept": "application/json",
                "X-Forwarded-For": "Included when behind proxy"
            }
        }
    
    def _get_methods_summary(self, routes_by_blueprint):
        """Get summary of HTTP methods used."""
        methods = {}
        
        for routes in routes_by_blueprint.values():
            for route in routes:
                for method in route['methods']:
                    methods[method] = methods.get(method, 0) + 1
        
        return methods
    
    def get_endpoint_tree(self, app):
        """Get a simplified tree view of endpoints."""
        tree = {}
        
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static':
                continue
            
            endpoint = rule.endpoint
            blueprint = endpoint.split('.')[0] if '.' in endpoint else 'root'
            
            if blueprint not in tree:
                tree[blueprint] = {
                    "methods": {},
                    "count": 0
                }
            
            path = str(rule)
            for method in rule.methods - {'OPTIONS', 'HEAD'}:
                if method not in tree[blueprint]["methods"]:
                    tree[blueprint]["methods"][method] = []
                
                tree[blueprint]["methods"][method].append(path)
                tree[blueprint]["count"] += 1
        
        return tree
    
    def get_endpoint_details(self, app, endpoint):
        """Get detailed information about a specific endpoint."""
        try:
            view_func = app.view_functions.get(endpoint)
            
            if not view_func:
                return None
            
            # Find the rule for this endpoint
            rule = None
            for r in app.url_map.iter_rules():
                if r.endpoint == endpoint:
                    rule = r
                    break
            
            if not rule:
                return None
            
            details = {
                "endpoint": endpoint,
                "path": str(rule),
                "methods": list(rule.methods - {'OPTIONS', 'HEAD'}),
                "description": self._extract_description(view_func),
                "auth": self._extract_auth_requirements(view_func),
                "parameters": self._extract_parameters(rule),
                "status_codes": self._extract_status_codes(view_func),
                "source_file": inspect.getfile(view_func) if hasattr(view_func, '__module__') else 'Unknown'
            }
            
            return details
        except Exception as e:
            return {"error": str(e)}
    
    def get_quick_reference(self, app):
        """Get a quick reference guide for common API tasks."""
        return {
            "quick_start": [
                {
                    "task": "User Login",
                    "endpoint": "POST /auth/login",
                    "description": "Authenticate user",
                    "example": {
                        "username": "user@example.com",
                        "password": "password"
                    }
                },
                {
                    "task": "Get User Profile",
                    "endpoint": "GET /auth/profile",
                    "description": "Retrieve current user profile",
                    "auth": "Session required"
                },
                {
                    "task": "List Posts",
                    "endpoint": "GET /posts",
                    "description": "Get all published posts",
                    "auth": "Public"
                },
                {
                    "task": "Create Post",
                    "endpoint": "POST /admin/posts",
                    "description": "Create new post",
                    "auth": "Administrator required"
                }
            ],
            "rate_limiting": {
                "admin": "Higher limits for admin endpoints",
                "public": "Standard rate limits",
                "static": "No rate limiting for static files"
            },
            "response_format": {
                "success": {
                    "status": 200,
                    "data": "Response data"
                },
                "error": {
                    "status": "Error code",
                    "message": "Error description"
                }
            }
        }
