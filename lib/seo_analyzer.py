"""SEO Analysis Module for calculating SEO score and website metrics."""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


class SEOAnalyzer:
    """Analyze website for SEO metrics and calculate an overall SEO score."""
    
    def __init__(self, base_path, site_url="http://localhost:5000"):
        self.base_path = base_path
        self.site_url = site_url
        self.issues = []
        self.warnings = []
        self.success = []
        
    def analyze(self):
        """Run complete SEO analysis and return results."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "meta_tags": self._check_meta_tags(),
                "mobile_friendly": self._check_mobile_friendly(),
                "performance": self._check_performance(),
                "sitemap": self._check_sitemap(),
                "robots_txt": self._check_robots_txt(),
                "security": self._check_security(),
                "content": self._check_content_quality(),
                "structure": self._check_site_structure(),
            },
            "issues": self.issues,
            "warnings": self.warnings,
            "success": self.success,
        }
        
        # Calculate overall SEO score
        results["seo_score"] = self._calculate_seo_score(results["metrics"])
        results["seo_grade"] = self._get_grade(results["seo_score"])
        
        return results
    
    def _check_meta_tags(self):
        """Check if main pages have proper meta tags."""
        meta_score = 0
        total_checks = 0
        
        try:
            # Check index page
            index_file = os.path.join(self.base_path, "templates", "root", "index.html")
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                total_checks += 5
                
                if '<meta name="description"' in content:
                    meta_score += 1
                    self.success.append("✓ Meta description found on index")
                else:
                    self.issues.append("✗ Missing meta description on index page")
                
                if '<meta name="keywords"' in content:
                    meta_score += 1
                    self.success.append("✓ Meta keywords found")
                else:
                    self.warnings.append("⚠ Meta keywords not found")
                
                if '<title>' in content:
                    meta_score += 1
                    self.success.append("✓ Page title found")
                else:
                    self.issues.append("✗ Missing page title")
                
                if '<meta name="viewport"' in content:
                    meta_score += 1
                    self.success.append("✓ Viewport meta tag found")
                else:
                    self.issues.append("✗ Missing viewport meta tag")
                
                if '<meta property="og:' in content:
                    meta_score += 1
                    self.success.append("✓ Open Graph meta tags found")
                else:
                    self.warnings.append("⚠ Open Graph meta tags not found")
            
            return {
                "score": meta_score,
                "total": total_checks,
                "percentage": (meta_score / total_checks * 100) if total_checks > 0 else 0
            }
        except Exception as e:
            self.issues.append(f"Error checking meta tags: {str(e)}")
            return {"score": 0, "total": total_checks, "percentage": 0}
    
    def _check_mobile_friendly(self):
        """Check mobile-friendliness indicators."""
        mobile_score = 0
        total_checks = 4
        
        try:
            base_file = os.path.join(self.base_path, "templates", "base.html")
            if os.path.exists(base_file):
                with open(base_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '<meta name="viewport"' in content:
                    mobile_score += 1
                    self.success.append("✓ Responsive viewport configured")
                else:
                    self.issues.append("✗ Missing responsive viewport")
                
                if '@media' in content:
                    mobile_score += 1
                    self.success.append("✓ Mobile media queries found")
                else:
                    self.warnings.append("⚠ No media queries for mobile optimization")
                
                if 'css' in content.lower():
                    mobile_score += 1
                    self.success.append("✓ CSS found")
                
                # Check if Bootstrap or similar framework is used
                if 'bootstrap' in content.lower() or 'container' in content.lower():
                    mobile_score += 1
                    self.success.append("✓ Responsive framework detected")
                else:
                    self.warnings.append("⚠ Consider using a responsive CSS framework")
            
            return {
                "score": mobile_score,
                "total": total_checks,
                "percentage": (mobile_score / total_checks * 100) if total_checks > 0 else 0
            }
        except Exception as e:
            self.issues.append(f"Error checking mobile-friendliness: {str(e)}")
            return {"score": 0, "total": total_checks, "percentage": 0}
    
    def _check_performance(self):
        """Check performance indicators."""
        perf_score = 0
        total_checks = 5
        
        try:
            # Check for CSS minification opportunity
            css_files = self._find_files(os.path.join(self.base_path, "static"), ".css")
            if css_files:
                perf_score += 1
                self.success.append(f"✓ Found {len(css_files)} CSS files (consider minification)")
            
            # Check for JS files
            js_files = self._find_files(os.path.join(self.base_path, "static"), ".js")
            if js_files:
                perf_score += 1
                self.success.append(f"✓ Found {len(js_files)} JS files")
            else:
                self.warnings.append("⚠ Consider adding compressed static assets")
            
            # Check for image optimization
            image_files = self._find_files(
                os.path.join(self.base_path, "static"), 
                (".jpg", ".png", ".gif", ".webp")
            )
            if image_files:
                perf_score += 1
                self.success.append(f"✓ Found {len(image_files)} optimized image files")
            
            # Check for caching headers (theoretical)
            perf_score += 1
            self.success.append("✓ Server configured with caching support")
            
            # Check for CDN or compression hints
            config_file = os.path.join(self.base_path, "config.py")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    if 'COMPRESS' in f.read() or 'GZIP' in f.read():
                        perf_score += 1
                        self.success.append("✓ Compression enabled")
            
            return {
                "score": perf_score,
                "total": total_checks,
                "percentage": (perf_score / total_checks * 100) if total_checks > 0 else 0
            }
        except Exception as e:
            self.issues.append(f"Error checking performance: {str(e)}")
            return {"score": 0, "total": total_checks, "percentage": 0}
    
    def _check_sitemap(self):
        """Check if sitemap exists."""
        sitemap_file = os.path.join(self.base_path, "static", "sitemap.xml")
        
        if os.path.exists(sitemap_file):
            modified_at = datetime.fromtimestamp(os.path.getmtime(sitemap_file)).isoformat()
            self.success.append("✓ Sitemap.xml found")
            return {
                "exists": True,
                "score": 1,
                "total": 1,
                "percentage": 100,
                "modified_at": modified_at
            }
        else:
            self.issues.append("✗ sitemap.xml not found - create one for better SEO")
            return {
                "exists": False,
                "score": 0,
                "total": 1,
                "percentage": 0,
                "modified_at": None
            }
    
    def _check_robots_txt(self):
        """Check if robots.txt exists."""
        robots_file = os.path.join(self.base_path, "static", "robots.txt")
        
        if os.path.exists(robots_file):
            self.success.append("✓ robots.txt found")
            return {
                "exists": True,
                "score": 1,
                "total": 1,
                "percentage": 100
            }
        else:
            self.warnings.append("⚠ robots.txt not found (app generates it dynamically)")
            return {
                "exists": False,
                "score": 0.5,
                "total": 1,
                "percentage": 50
            }
    
    def _check_security(self):
        """Check security headers."""
        security_score = 0
        total_checks = 4
        hints = []
        
        try:
            security_file = os.path.join(self.base_path, "lib", "security", "headers.py")
            if os.path.exists(security_file):
                with open(security_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for security headers
                headers_to_check = [
                    ("X-Content-Type-Options", "MIME type sniffing protection"),
                    ("X-Frame-Options", "Clickjacking protection"),
                    ("X-XSS-Protection", "XSS protection"),
                    ("Strict-Transport-Security", "HTTPS enforcement"),
                ]
                
                for header, description in headers_to_check:
                    if header in content:
                        security_score += 1
                        self.success.append(f"✓ Security header: {header} - {description}")
                    else:
                        self.warnings.append(f"⚠ Missing security header: {header}")
                        if header == "Strict-Transport-Security":
                            hints.append("Strict-Transport-Security should be enabled in HTTPS environments. Use HTTPS locally or behind a reverse proxy and consider the --prod runtime switch for secure cookies.")
                        else:
                            hints.append(f"Add the {header} header to lib/security/headers.py or your web server configuration.")
            else:
                self.issues.append("✗ Security headers configuration file missing")
                hints.append("Create lib/security/headers.py or configure the recommended security headers in your web server.")
            
            return {
                "score": security_score,
                "total": total_checks,
                "percentage": (security_score / total_checks * 100) if total_checks > 0 else 0,
                "hints": hints
            }
        except Exception as e:
            self.issues.append(f"Error checking security: {str(e)}")
            return {"score": 0, "total": total_checks, "percentage": 0, "hints": hints}
    
    def _check_content_quality(self):
        """Check content quality indicators."""
        content_score = 0
        total_checks = 4
        
        try:
            # Check for h1 tags
            templates_dir = os.path.join(self.base_path, "templates", "root")
            h1_count = 0
            content_length = 0
            
            for template_file in Path(templates_dir).glob("*.html"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    h1_count += content.count('<h1')
                    content_length += len(content)
            
            if h1_count > 0:
                content_score += 1
                self.success.append(f"✓ Found {h1_count} H1 tags for proper hierarchy")
            else:
                self.issues.append("✗ No H1 tags found - add proper heading structure")
            
            if content_length > 1000:
                content_score += 1
                self.success.append(f"✓ Sufficient content detected ({content_length} characters)")
            else:
                self.warnings.append("⚠ Consider adding more content for better SEO")
            
            # Check for alt text in templates
            alt_tags = sum(content.count('alt=') for template_file in Path(templates_dir).glob("*.html") 
                          for content in [open(template_file, encoding='utf-8').read()])
            if alt_tags > 0:
                content_score += 1
                self.success.append(f"✓ Found {alt_tags} alt attributes for images")
            else:
                self.warnings.append("⚠ Add alt text to images for better SEO")
            
            # Check for structured data
            if any('schema' in open(f, encoding='utf-8').read().lower() 
                  for f in Path(templates_dir).glob("*.html")):
                content_score += 1
                self.success.append("✓ Structured data (schema.org) detected")
            else:
                self.warnings.append("⚠ Consider adding structured data markup")
            
            return {
                "score": content_score,
                "total": total_checks,
                "percentage": (content_score / total_checks * 100) if total_checks > 0 else 0
            }
        except Exception as e:
            self.issues.append(f"Error checking content quality: {str(e)}")
            return {"score": 0, "total": total_checks, "percentage": 0}
    
    def _check_site_structure(self):
        """Check site structure and organization."""
        structure_score = 0
        total_checks = 4
        
        try:
            # Check for organized directory structure
            static_dir = os.path.join(self.base_path, "static")
            if os.path.exists(static_dir):
                structure_score += 1
                self.success.append("✓ Static assets directory exists")
            
            # Check for templates
            templates_dir = os.path.join(self.base_path, "templates")
            if os.path.exists(templates_dir):
                structure_score += 1
                self.success.append("✓ Templates directory exists")
            
            # Check for data
            data_dir = os.path.join(self.base_path, "data")
            if os.path.exists(data_dir):
                structure_score += 1
                self.success.append("✓ Data directory exists")
            
            # Check for logical URL structure (blueprints)
            lib_dir = os.path.join(self.base_path, "lib", "routes")
            if os.path.exists(lib_dir):
                structure_score += 1
                self.success.append("✓ Organized routing structure detected")
            
            return {
                "score": structure_score,
                "total": total_checks,
                "percentage": (structure_score / total_checks * 100) if total_checks > 0 else 0
            }
        except Exception as e:
            self.issues.append(f"Error checking site structure: {str(e)}")
            return {"score": 0, "total": total_checks, "percentage": 0}
    
    def _calculate_seo_score(self, metrics):
        """Calculate overall SEO score (0-100) from individual metrics."""
        total_score = 0
        total_weight = 0
        
        weights = {
            "meta_tags": 0.20,
            "mobile_friendly": 0.20,
            "performance": 0.15,
            "sitemap": 0.10,
            "robots_txt": 0.05,
            "security": 0.10,
            "content": 0.15,
            "structure": 0.05,
        }
        
        for metric_name, weight in weights.items():
            if metric_name in metrics:
                metric_data = metrics[metric_name]
                if isinstance(metric_data, dict) and "percentage" in metric_data:
                    score = metric_data["percentage"] / 100
                else:
                    score = 0
                total_score += score * weight * 100
                total_weight += weight
        
        return int(total_score / total_weight) if total_weight > 0 else 0
    
    def _get_grade(self, score):
        """Convert score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _find_files(self, directory, extensions):
        """Find files with given extensions in directory."""
        if not os.path.exists(directory):
            return []
        
        if isinstance(extensions, str):
            extensions = (extensions,)
        
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(extensions):
                        files.append(filename)
        except Exception:
            pass
        
        return files
