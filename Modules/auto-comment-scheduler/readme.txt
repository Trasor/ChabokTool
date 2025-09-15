=== Auto Comment Scheduler By Donooco ===
Contributors: Ahmadreza Khatami, donooco (Donooco.com)
Tags: comments, scheduler, automation, persian date, wp-cron
Requires at least: 5.0
Tested up to: 6.5
Stable tag: 2.0
Requires PHP: 7.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Schedule comments and replies automatically for your WordPress posts and products with Persian date support.

== Description ==

**Auto Comment Scheduler By Donooco** is a powerful WordPress plugin that allows you to schedule comments and replies for your posts and products automatically. Whether you want to boost user engagement or publish comments at specific times, this plugin makes it easy and efficient.

### Key Features
- Schedule comments and replies for posts and products.
- Supports Persian (Jalali) date for Iranian users.
- Displays a history of scheduled comments.
- User-friendly interface with a metabox in the post/product edit screen.
- Integrates with WP-Cron for automated publishing.
- Debug logging for troubleshooting.

This plugin is ideal for site administrators who want to automate comment publishing while maintaining control over the timing and content.

== Installation ==

1. Upload the `auto-comment-scheduler` folder to the `/wp-content/plugins/` directory, or install the plugin directly through the WordPress plugins screen.
2. Activate the plugin through the 'Plugins' screen in WordPress.
3. A new metabox titled "Auto Comment Scheduler" will appear on the post and product edit screens (for administrators only).

== Usage ==

1. Go to the edit screen of a post or product.
2. Find the "Auto Comment Scheduler" metabox.
3. Fill in the form:
   - Comment Author Name
   - Comment Author Email
   - Comment Content
   - Reply Author Name
   - Reply Author Email
   - Reply Content
   - Publish Date (Persian format: YYYY/MM/DD, e.g., 1404/01/20)
   - Publish Time (HH:MM, e.g., 14:30)
4. Click the "Schedule" button to schedule the comment and reply.
5. The comment will be published at the specified time, and the reply will be published 10 minutes later.
6. View the history of scheduled comments in the metabox.

== Frequently Asked Questions ==

= Can I schedule multiple comments for the same post? =
Yes, you can schedule as many comments and replies as you want for each post or product.

= Does the plugin support Gregorian dates? =
Currently, the plugin only supports Persian (Jalali) dates, but they are automatically converted to Gregorian dates for scheduling.

= How can I cancel a scheduled comment? =
You can use a plugin like WP Crontrol to view and delete scheduled events.

= What if my comments are not being published? =
Ensure that WP-Cron is enabled on your site. You can also set up a real cron job on your server for more reliable scheduling. Check the debug log (`wp-content/debug.log`) for any errors.

== Screenshots ==

1. The "Auto Comment Scheduler" metabox on the post edit screen.
2. Scheduling a comment with Persian date and time.
3. Viewing the history of scheduled comments.

== Changelog ==

= 2.0 =
* Added support for scheduling replies as child comments.
* Improved Persian date validation and conversion.
* Enhanced debug logging for better troubleshooting.
* Fixed various bugs and improved performance.

= 1.0 =
* Initial release with basic comment scheduling functionality.

== Upgrade Notice ==

= 2.0 =
This version includes major improvements in reply scheduling and Persian date handling. Please test on a staging site before updating on a live site.

== Support ==
For support, please contact us at:  
**Info@donooco.com**  
Or visit our website:  
**https://donooco.com**