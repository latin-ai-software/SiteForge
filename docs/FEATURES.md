# SiteForge - Complete Feature Documentation

SiteForge is a comprehensive, feature-rich website platform designed to empower content creators, publishers, and site administrators with powerful tools for managing, monetizing, and optimizing their online presence.

---

## 📋 Table of Contents

1. [General Settings](#general-settings)
2. [Content Management](#content-management)
3. [Media & Slideshow](#media--slideshow)
4. [User & Role Management](#user--role-management)
5. [SEO & Search Optimization](#seo--search-optimization)
6. [Analytics & Tracking](#analytics--tracking)
7. [Security & Privacy](#security--privacy)
8. [Email & Newsletter](#email--newsletter)
9. [Social Media Integration](#social-media-integration)
10. [Theme Customization](#theme-customization)
11. [Backup & Disaster Recovery](#backup--disaster-recovery)
12. [System Management](#system-management)
13. [Developer Tools](#developer-tools)

---

## 🎯 General Settings

Customize the core identity and basic configuration of your website.

### Site Identity
- **Site Title** - Your website's primary name and heading
- **Site Description** - Meta description for search engines and social media (SEO)
- **Meta Keywords** - Comma-separated keywords for search engine optimization
- **Domain** - Primary domain URL for your website
- **Posts Per Page** - Control pagination (1-100 posts per page)

### Favicon & Branding
- **Favicon Upload** - Custom website icon displayed in browser tabs
  - Supported formats: PNG, JPG, JPEG, GIF, ICO
- **Embed Favicon in HTML** - Embed favicon data directly in page source
- **Header Background Image** - JPG image for page header background
  - Toggle header background visibility independently

### Legal & Compliance
- **Imprint (Legal Notice)** - Upload HTML file containing legal disclaimers and business information
- **Imprint Display Toggle** - Show/hide imprint page visibility

---

## 📝 Content Management

Create, organize, and publish rich media content with advanced features.

### Post Management
- **Create Posts** - Write new blog posts and articles
- **Edit Posts** - Modify existing published or draft content
- **Delete Posts** - Remove posts from your site
- **Post Metadata**
  - Title - Post heading
  - Rich Text Content - WYSIWYG editor (Quill) with formatting
  - Categories - Assign multiple categories per post
  - Tags - Add searchable tags to content
  - Author - Assign or change post author
  - Status - Publish as live, draft, or scheduled
  - Attachments - Upload and attach files to posts

### Interactive Surveys & Polls
- **Add Surveys to Posts** - Include polls within post content
  - Survey Question - Custom question text
  - Multiple Options - Add unlimited survey choices
  - Vote Tracking - Real-time vote count and percentages
  - Results Display - Show live results to visitors

### Git Repository Integration (Optional Plugin)
- **Link Posts to Git Repositories** - Associate posts with code repositories
- **Release Tags** - Link posts to specific Git release versions
- **Automated Linking** - Sync posts with repository releases

### Comment Management
- **Require Comment Approval** - Moderate comments before display
- **View & Manage Comments** - Dedicated comment dashboard
- **Delete Comments** - Remove individual comments
- **Bulk Operations** - Delete all read comment notifications
- **Comment Statistics** - Track total comments

---

## 🖼️ Media & Slideshow

Manage rich multimedia content and dynamic homepage presentations.

### Media Library
- **Upload Media Files** - Add images, PDFs, and documents
- **Organize Media** - Browse by file type and upload date
- **File Management**
  - Rename files - Change filenames
  - Delete files - Remove unused media
  - View metadata - Size, usage information
  - Track usage - See which posts use specific files
  - Identify unused files - Find files not in any post

### Advanced Filtering
- **Filter by Name** - Search media files by filename
- **Filter by File Type** - PNG, JPG, JPEG, PDF, and more
- **Filter by Upload Date** - Today, Last 7 days, Last 30 days

### Homepage Slideshow
- **Enable/Disable Slideshow** - Toggle slideshow functionality
- **Slideshow Configuration**
  - Auto-advance interval (3-120 seconds)
  - Custom header/title text
  - Subtitle/description text
  - Background image (JPG/PNG)
- **Slide Management**
  - Upload multiple PNG slide images
  - Remove individual slides
  - Preview slides before publishing
  - Automatic rotation through slides

---

## 👥 User & Role Management

Control user access and permissions across your platform.

### User Accounts
- **User Registration** - Enable/disable public sign-ups
- **Create Users** - Manually add new user accounts
- **Delete Users** - Remove user accounts
- **Password Management**
  - Allow user password changes
  - Admin password reset - Reset user passwords
  - Password strength requirements

### User Roles & Permissions
- **Create Custom Roles** - Define custom role types with specific permissions
- **Assign Roles** - Change user role and permission levels
- **Role-based Access Control** - Different dashboards for different roles:
  - Admin - Full system access
  - Editor/Author - Content creation and media management
  - Guest/Viewer - Limited or no dashboard access

### Account Status
- **Lock/Unlock Users** - Disable/enable user accounts
- **View User Details** - Account creation date, role assignments, last login
- **Bulk User Management** - Manage multiple users efficiently

### Git Integration (Optional)
- **Grant Git Access** - Allow users to access Git repositories
- **Revoke Git Access** - Remove repository permissions

---

## 🔍 SEO & Search Optimization

Optimize your site for search engines and improve discoverability.

### Search Engine Configuration
- **Enable/Disable Indexing** - Allow or block search engine crawling
- **Robot User-Agents** - Specify which bots can crawl:
  - All bots: `*`
  - Specific bots: Googlebot, Bingbot, etc.
  - robots.txt generation

### Automated SEO Analysis
- **SEO Dashboard** - Comprehensive health check of SEO metrics
- **Analysis Categories**
  - Meta descriptions - Check and add missing SEO descriptions
  - Title tags - Verify page titles
  - Meta keywords - Check keyword coverage
  - Open Graph tags - Social media sharing optimization
  - Viewport meta tag - Mobile responsiveness

### Sitemap Management
- **Generate Sitemap** - Create XML sitemap for search engines
- **Refresh Sitemap** - Update sitemap after content changes
- **View Sitemap History** - Track previous sitemap generations
- **Modified Timestamps** - Show last-modified dates in sitemap

### SEO Recommendations
- **Quick Fixes** - One-click solutions for common SEO issues
- **Improvement Suggestions** - Get actionable recommendations
- **Analysis History** - Track SEO improvements over time
- **Robots.txt Generation** - Automatically create robots.txt file

---

## 📊 Analytics & Tracking

Measure and understand visitor behavior and traffic patterns.

### Analytics Provider
- **Built-in Analytics** - Native visitor tracking without external services
- **Google Analytics** - Integration with Google Analytics
  - Tracking ID configuration (GA-XXXXXXXXX or G-XXXXXXXXX)

### Analytics Dashboard
- **Enable/Disable Analytics** - Toggle tracking on/off
- **Tracking Period** - Customize analysis window (1-365 days)
- **Visitor Statistics**
  - Total visitor count
  - Visitor trends over time
  - Unique vs returning visitors

### Visitor Details
- **Recent Visitors List** - Track individual visits with:
  - IP address
  - Visit timestamp
  - User-agent / Browser info
  - Visited pages
  - Referrer information

### Cookie & Consent Automation
- **Auto-require Consent** - Automatically enable cookie banner when analytics enabled
- **Analytics Privacy** - Compliant visitor tracking

---

## 🔒 Security & Privacy

Protect your site and visitors with comprehensive security features.

### Age Gate & Content Restrictions
- **Enable Age Gate Popup** - Show age verification for 18+ content
- **Site Rating System** - Content ratings for appropriate filtering:
  - **G** - All ages appropriate
  - **PG-13** - Not recommended for children under 13
  - **R** - Not recommended for children under 17
  - **18+** - Adults only content
- **Age Gate Disclaimer** - Legal warning displayed to visitors
- **Age Verification Tracking** - Track which visitors accepted age gate

### Cookie & Consent Management
- **Cookie Consent Banner** - Customizable cookie notice
- **Cookie Consent Message** - Custom HTML text for cookie notice
- **Compliance Automation** - Auto-require consent when needed
- **Visitor Consent Tracking** - Track visitor consent preferences
- **Legal Compliance** - GDPR and privacy regulation ready

---

## 📧 Email & Newsletter

Build and manage your email subscriber base.

### Newsletter Configuration
- **Enable/Disable Newsletter** - Toggle newsletter functionality
- **Newsletter Sender Email** - Set "from" email address for newsletters
- **Email Service Integration** - Amazon SES SMTP configuration:
  - SMTP Hostname
  - SMTP Port (1-65535)
  - Authentication username and password

### Newsletter Management
- **Send Newsletter** - Broadcast messages to all subscribers
- **Subscriber List** - View all newsletter subscribers
- **Subscription Tracking** - Track subscriber growth over time
- **SMTP Testing** - Verify email service connection

---

## 🌐 Social Media Integration

Connect your site with social media platforms.

### Social Media Links
- **Show Social Icons** - Display/hide social media icons on site
- **Twitter/X Integration**
  - Add Twitter handle (@username)
  - Link to Twitter profile
- **Facebook Integration**
  - Add Facebook page URL
  - Link to Facebook business page
- **YouTube Integration**
  - YouTube channel URL support
  - YouTube channel ID support (UC... format)
  - YouTube @handle support
  - Multiple format compatibility

---

## 🎨 Theme Customization

Design and customize your site's visual appearance.

### Theme Management
- **View Available Themes** - Browse installed themes
- **Switch Themes** - Activate different theme designs
- **Delete Themes** - Remove unused themes

### Theme Creation & Editing
- **Create New Theme** - Design custom color schemes
  - Theme name
  - Color variables (primary, secondary, background, text, etc.)
  - Typography settings
  - Responsive design options
- **Edit Existing Themes** - Modify theme CSS variables
- **Live Preview** - See theme changes in real-time

### Theme Features
- **Responsive Design** - Mobile-friendly layouts
- **Dark Mode Support** - Light and dark color schemes
- **Custom Branding** - Match your brand colors

---

## 💾 Backup & Disaster Recovery

Protect your data with comprehensive backup solutions.

### Local Backups
- **Create Backup** - Generate immediate local backup
- **View Backup List** - List all backups with size and date
- **Download Backup** - Download backup files to your computer
- **Delete Backups** - Remove old or unwanted backups
- **Auto-Cleanup** - Automatically keep only 10 most recent backups
- **Backup Scheduling** - Schedule automatic daily/weekly backups

### Remote Backups via SCP (Secure Copy)
- **Enable/Disable SCP Backup** - Toggle SCP uploads
- **SCP Configuration**
  - Remote server hostname
  - SSH port (default 22)
  - Authentication username and password
  - Remote destination directory
- **Test Connection** - Verify SCP connection before enabling
- **Automatic Uploads** - Auto-upload backups to remote server

### Remote Backups via FTP
- **Enable/Disable FTP Backup** - Toggle FTP uploads
- **FTP Configuration**
  - FTP server hostname
  - FTP port (default 21)
  - Authentication username and password
  - Remote destination directory
- **Automatic Uploads** - Auto-upload backups to remote FTP server

### Remote Backups via HTTPS
- **Enable/Disable HTTPS Backup** - Toggle HTTPS uploads
- **HTTPS Configuration**
  - Upload endpoint URL
  - API authentication token
- **Custom Endpoints** - Support for custom backup services

---

## ⚙️ System Management

Manage core system operations and configurations.

### Cache Management
- **Cache Statistics** - View cache performance metrics:
  - Cache hits and misses
  - Memory usage and limits
  - Per-cache breakdowns
- **Flush Cache** - Clear all cached data
- **Cache Optimization** - Automatic cache management

### System Updates
- **Check for Updates** - Scan for new SiteForge versions
- **Install Updates** - Download and apply updates
- **Update Progress Tracking** - Monitor installation progress
- **View Version Info** - Current and latest version numbers
- **Auto-Restart** - Automatic service restart after updates

### Plugin Management
- **Enable/Disable Plugins** - Toggle individual plugins on/off
- **View Available Plugins** - List all installed plugins
- **Plugin Configuration** - Configure plugin settings
- **Auto-Restart on Plugin Change** - Automatic service restart when changing plugins

### Encryption
- **View Encryption Status** - Check if configuration files are encrypted
- **Enable Encryption** - Encrypt sensitive configuration data
- **Disable Encryption** - Decrypt configuration files for editing
- **Data Protection** - Secure sensitive settings like API keys and passwords

---

## 🔔 Notifications

Manage admin notifications and alerts.

### Notification Center
- **View All Notifications** - Centralized notification dashboard
- **Notification Types** - Info, success, warning, and error messages
- **Unread Count** - Badge showing unread notifications

### Notification Management
- **Create Notifications** - Send manual notifications to admins
  - Notification title
  - Custom message text
  - Message type selection
- **Mark as Read** - Mark individual notifications read
- **Bulk Mark as Read** - Mark all notifications read at once
- **Delete Notifications** - Remove individual notifications
- **Bulk Delete** - Delete all read notifications at once
- **Real-time Updates** - Instant notification display

---

## 🛠️ Developer Tools

Advanced tools for developers and technical administrators.

### API Documentation
- **API Endpoints** - View all available API endpoints
- **API Authentication** - Token and key management
- **API Usage Examples** - Sample requests and responses
- **Rate Limiting Info** - API rate limits and quotas

### Template Management
- **HTML Templates** - Edit site templates directly
- **Template Editing** - Modify template layouts and structure
- **Template Variables** - Available template variables reference
- **Preview Templates** - Test template changes

### Admin Help & Documentation
- **Admin Documentation** - Built-in help system
- **Feature Guides** - Step-by-step feature walkthroughs
- **Troubleshooting** - Common issues and solutions
- **Support Links** - Access to support resources

---

## 📈 Feature Summary

### Total Configurable Settings: **80+**

**By Access Level:**
- **Admin-only:** Settings, Users, Analytics, Backups, SEO, Themes, Cache, Updates, Encryption, Notifications
- **Editor/Author:** Post creation, Content management, Media uploads
- **Viewer:** Newsletter subscription, Comments (if enabled)

**By Category:**
- **Content Creation:** 7 categories with 40+ options
- **Site Configuration:** 5 categories with 20+ options
- **Security & Compliance:** 3 categories with 15+ options
- **Performance & Monitoring:** 3 categories with 10+ options
- **Integrations:** 2 categories with 8+ options

---

## 🚀 Getting Started

1. **Setup** - Configure general settings (site title, domain, etc.)
2. **Theme** - Choose and customize your site theme
3. **Content** - Create your first posts and pages
4. **Media** - Upload images and media files
5. **SEO** - Configure search engine settings
6. **Analytics** - Enable tracking and monitoring
7. **Security** - Configure privacy and consent settings
8. **Backup** - Setup automated backups
9. **Newsletter** - Configure email settings (optional)
10. **Publish** - Go live and start attracting visitors

---

## 📞 Support

For detailed setup guides and troubleshooting, visit the [SiteForge Documentation](../README.md) or contact your administrator.

---

**SiteForge** - Empowering content creators worldwide. Version: Latest
