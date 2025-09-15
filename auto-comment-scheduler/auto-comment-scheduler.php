<?php
/*
Plugin Name: Auto Comment Scheduler By Donooco
Description: A plugin to schedule comments and replies automatically in WordPress.
Version: 2.9.1
Author: Ahmadreza Khatami (CEO of Donooco Agency)
Author URI: https://donooco.com
*/

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

// Create table for comment history on plugin activation
register_activation_hook(__FILE__, 'acs_create_history_table');
function acs_create_history_table() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE $table_name (
        id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
        post_id BIGINT(20) UNSIGNED NOT NULL,
        comment_author VARCHAR(255) NOT NULL,
        comment_email VARCHAR(255) NOT NULL,
        comment_content TEXT NOT NULL,
        reply_author VARCHAR(255) NOT NULL,
        reply_email VARCHAR(255) NOT NULL,
        reply_content TEXT NOT NULL,
        scheduled_time DATETIME NOT NULL,
        transient_key VARCHAR(255) NOT NULL,
        ip_address VARCHAR(45) DEFAULT NULL,
        comment_id BIGINT(20) DEFAULT NULL,
        is_published TINYINT(1) DEFAULT 0,
        PRIMARY KEY (id),
        INDEX idx_scheduled_time (scheduled_time),
        INDEX idx_post_id (post_id)
    ) $charset_collate;";

    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    $result = dbDelta($sql);

    if ($result === false) {
        error_log('Failed to create table ' . $table_name . ': ' . $wpdb->last_error);
    } else {
        error_log('Table ' . $table_name . ' created successfully');
    }

    update_option('acs_db_version', '2.9');
}

// Create table for custom transients on plugin activation
register_activation_hook(__FILE__, 'acs_create_transient_table');
function acs_create_transient_table() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_transients';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE IF NOT EXISTS $table_name (
        transient_key VARCHAR(191) NOT NULL,
        transient_value LONGTEXT NOT NULL,
        expiration BIGINT(20) NOT NULL,
        PRIMARY KEY (transient_key),
        INDEX idx_expiration (expiration)
    ) $charset_collate;";

    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    dbDelta($sql);
}


add_action('wp_cron', 'acs_log_cron_execution');
function acs_log_cron_execution() {
    error_log('WP-Cron executed at: ' . date('Y-m-d H:i:s') . ' UTC');
}


// Function to clean up expired transients
function acs_cleanup_expired_transients() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_transients';
    $current_time = time();

    error_log('Cleaning up expired transients at: ' . date('Y-m-d H:i:s', $current_time));

    $expired_transients = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT transient_key FROM $table_name WHERE expiration < %d",
            $current_time
        ),
        ARRAY_A
    );

    if ($expired_transients === false) {
        error_log('Error fetching expired transients: ' . $wpdb->last_error);
        return 0;
    }

    $deleted_count = 0;
    foreach ($expired_transients as $transient) {
        $transient_key = $transient['transient_key'];
        $result = $wpdb->delete(
            $table_name,
            ['transient_key' => $transient_key],
            ['%s']
        );
        if ($result !== false) {
            error_log('Deleted expired transient: ' . $transient_key);
            $deleted_count += $result;
        } else {
            error_log('Failed to delete transient ' . $transient_key . ': ' . $wpdb->last_error);
        }
    }

    return $deleted_count;
}

// Schedule daily cleanup of expired transients at a low-traffic time (e.g., 3 AM Asia/Tehran)
if (!wp_next_scheduled('acs_cleanup_transients')) {
    // Calculate the next 3 AM in Asia/Tehran
    $timezone = new DateTimeZone('Asia/Tehran');
    $now = new DateTime('now', $timezone);
    $next_3am = new DateTime('tomorrow 3:00', $timezone);
    if ($now->format('H') >= 3) {
        $next_3am->modify('+1 day');
    }
    $timestamp = $next_3am->getTimestamp();
    wp_schedule_event($timestamp, 'daily', 'acs_cleanup_transients');
}
add_action('acs_cleanup_transients', 'acs_cleanup_expired_transients');

// Clean up on plugin deactivation
register_deactivation_hook(__FILE__, 'acs_deactivate');
function acs_deactivate() {
    wp_clear_scheduled_hook('acs_cleanup_transients');

    // Optionally, drop the custom transients table
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_transients';
    $wpdb->query("DROP TABLE IF EXISTS $table_name");
}

// Add settings page under Tools menu
add_action('admin_menu', 'acs_add_settings_page');
function acs_add_settings_page() {
    add_submenu_page(
        'tools.php',
        'تنظیمات کامنت اتوماتیک',
        'تنظیمات کامنت اتوماتیک',
        'manage_options',
        'acs-settings',
        'acs_settings_page_callback'
    );
}

// Settings page callback
function acs_settings_page_callback() {
    // Save settings if form is submitted
    if (isset($_POST['acs_settings_nonce']) && wp_verify_nonce($_POST['acs_settings_nonce'], 'acs_settings_nonce_action')) {
        $settings = [
            'reply_author' => sanitize_text_field($_POST['acs_reply_author']),
            'reply_email' => sanitize_email($_POST['acs_reply_email']),
            'date_time' => sanitize_textarea_field($_POST['acs_date_time']),
            'tone_details' => sanitize_textarea_field($_POST['acs_tone_details']),
            'extra_conditions' => sanitize_textarea_field($_POST['acs_extra_conditions']),
            'developer_mode' => isset($_POST['acs_developer_mode']) ? 1 : 0,
            'reply_delay_minutes' => isset($_POST['acs_reply_delay_minutes']) ? intval($_POST['acs_reply_delay_minutes']) : 10,
        ];
        update_option('acs_settings', $settings);
        echo '<div class="updated"><p>تنظیمات با موفقیت ذخیره شد!</p></div>';
    }

    // Get current settings
    $settings = get_option('acs_settings', [
        'reply_author' => '',
        'reply_email' => '',
        'date_time' => '',
        'tone_details' => '',
        'extra_conditions' => '',
        'developer_mode' => 0,
        'reply_delay_minutes' => 10,
    ]);
    ?>
    <div class="wrap">
        <h1>تنظیمات کامنت اتوماتیک</h1>
        <form method="post">
            <?php wp_nonce_field('acs_settings_nonce_action', 'acs_settings_nonce'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="acs_reply_author">نام پاسخ‌دهنده کامنت‌ها:</label></th>
                    <td>
                        <input type="text" id="acs_reply_author" name="acs_reply_author" class="regular-text" value="<?php echo esc_attr($settings['reply_author']); ?>">
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="acs_reply_email">ایمیل پاسخ‌دهنده کامنت‌ها:</label></th>
                    <td>
                        <input type="email" id="acs_reply_email" name="acs_reply_email" class="regular-text" value="<?php echo esc_attr($settings['reply_email']); ?>">
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="acs_date_time">پرامپت تاریخ و زمان و تعداد کامنت مورد نیاز:</label></th>
                    <td>
                        <textarea id="acs_date_time" name="acs_date_time" class="large-text" rows="5" placeholder="به طور مثال: به مدت 30 روز از تاریخ 22 اردیبهشت 1404 شروع کن و هر روز یه کامنت بزار ولی ساعتش به صورت رندوم دست خودت باشه (بین 9 صبح تا 12 شب)"><?php echo esc_textarea($settings['date_time']); ?></textarea>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="acs_tone_details">توضیحات لحن و موارد رعایت شده در کامنت‌ها:</label></th>
                    <td>
                        <textarea id="acs_tone_details" name="acs_tone_details" class="large-text" rows="5" placeholder="مثلا: لحن سوالات دوستانه و محاوره‌ای باشه اما پاسخ‌ها علمی و پر محتوا باشه"><?php echo esc_textarea($settings['tone_details']); ?></textarea>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="acs_extra_conditions">شرایط اضافی (اختیاری):</label></th>
                    <td>
                        <textarea id="acs_extra_conditions" name="acs_extra_conditions" class="large-text" rows="5" placeholder="مثلا: شرایط ارسال برای تهران 1 الی دو روز کاری و شهرستان 2 الی 3 روز کاری هست همینطور حواست باشه که ما تخفیف نداریم و تمام محصولاتمون اورجینال هست روی این تاکید داشته باش همیشه"><?php echo esc_textarea($settings['extra_conditions']); ?></textarea>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="acs_developer_mode">حالت دولوپر:</label></th>
                    <td>
                        <input type="checkbox" id="acs_developer_mode" name="acs_developer_mode" value="1" <?php checked($settings['developer_mode'], 1); ?>>
                        <span>فعال کردن حالت دولوپر (برای تست سریع زمان‌بندی‌ها)</span>
                    </td>
                </tr>
                <tr class="acs-developer-settings" style="display: <?php echo $settings['developer_mode'] ? 'table-row' : 'none'; ?>;">
                    <th scope="row"><label for="acs_reply_delay_minutes">زمان‌بندی اتوماتیک پاسخ (دقیقه):</label></th>
                    <td>
                        <input type="number" id="acs_reply_delay_minutes" name="acs_reply_delay_minutes" class="regular-text" value="<?php echo esc_attr($settings['reply_delay_minutes']); ?>" min="0">
                        <p class="description">تعداد دقیقه‌هایی که پاسخ بعد از سوال منتشر شود (پیش‌فرض: 10 دقیقه)</p>
                    </td>
                </tr>
            </table>
            <p class="submit">
                <input type="submit" class="button button-primary" value="ذخیره تنظیمات">
            </p>
        </form>
    </div>
    <script>
        jQuery(document).ready(function($) {
            $('#acs_developer_mode').on('change', function() {
                if ($(this).is(':checked')) {
                    $('.acs-developer-settings').show();
                } else {
                    $('.acs-developer-settings').hide();
                }
            });
        });
    </script>
    <?php
}

// Add settings link to plugin actions
add_filter('plugin_action_links_' . plugin_basename(__FILE__), 'acs_add_settings_link');
function acs_add_settings_link($links) {
    $settings_link = '<a href="' . admin_url('tools.php?page=acs-settings') . '">تنظیمات افزونه</a>';
    array_push($links, $settings_link);
    return $links;
}

// Enqueue scripts and styles for admin
add_action('admin_enqueue_scripts', 'acs_enqueue_scripts');
function acs_enqueue_scripts($hook) {
    if (!in_array($hook, ['post.php', 'post-new.php'])) {
        return;
    }

    wp_enqueue_script('jquery-ui-datepicker');
    wp_enqueue_style('jquery-ui-css', 'https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css');

    wp_enqueue_script('persian-datepicker', plugin_dir_url(__FILE__) . 'assets/persianDatepicker.min.js', ['jquery', 'jquery-ui-datepicker'], '1.0', true);
    wp_enqueue_style('persian-datepicker-css', plugin_dir_url(__FILE__) . 'assets/persianDatepicker-default.css', [], '1.0');

    wp_enqueue_style('font-awesome', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css', [], '5.15.4');

    wp_enqueue_script('acs-script', plugin_dir_url(__FILE__) . 'assets/acs-script.js', ['jquery', 'persian-datepicker'], '2.9', true);
    wp_enqueue_style('acs-style', plugin_dir_url(__FILE__) . 'assets/acs-style.css', [], '2.9');

    wp_localize_script('acs-script', 'acs_vars', [
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('acs_meta_box_nonce_action'),
        'get_comment_nonce' => wp_create_nonce('acs_get_comment_nonce'),
        'update_comment_nonce' => wp_create_nonce('acs_update_comment_nonce'),
        'generate_prompt_nonce' => wp_create_nonce('acs_generate_prompt_nonce'),
    ]);
}

// Add metabox to post/product edit screen
add_action('add_meta_boxes', 'acs_add_meta_box');
function acs_add_meta_box() {
    if (!current_user_can('manage_options')) {
        return;
    }

    $post_types = ['post', 'product'];
    add_meta_box(
        'acs_meta_box',
        'زمان‌بندی کامنت اتوماتیک',
        'acs_meta_box_callback',
        $post_types,
        'normal',
        'high'
    );
}

// Function to convert Gregorian to Jalali
function gregorian_to_jalali($g_y, $g_m, $g_d) {
    $g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    $j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29];

    $gy = $g_y - 1600;
    $gm = $g_m - 1;
    $gd = $g_d - 1;

    $g_day_no = 365 * $gy + floor(($gy + 3) / 4) - floor(($gy + 99) / 100) + floor(($gy + 399) / 400);

    for ($i = 0; $i < $gm; ++$i) {
        $g_day_no += $g_days_in_month[$i];
    }
    if ($gm > 1 && (($gy % 4 == 0 && $gy % 100 != 0) || ($gy % 400 == 0))) {
        $g_day_no++;
    }
    $g_day_no += $gd;

    $j_day_no = $g_day_no - 79;

    $j_np = floor($j_day_no / 12053);
    $j_day_no %= 12053;

    $jy = 979 + 33 * $j_np + 4 * floor($j_day_no / 1461);
    $j_day_no %= 1461;

    if ($j_day_no >= 366) {
        $jy += floor(($j_day_no - 1) / 365);
        $j_day_no = ($j_day_no - 1) % 365;
    }

    for ($i = 0; $i < 11 && $j_day_no >= $j_days_in_month[$i]; ++$i) {
        $j_day_no -= $j_days_in_month[$i];
    }

    $jm = $i + 1;
    $jd = $j_day_no + 1;

    return [$jy, $jm, $jd];
}

// Function to convert Jalali to Gregorian
function jalali_to_gregorian($j_y, $j_m, $j_d) {
    $j_y = (int)$j_y;
    $j_m = (int)$j_m;
    $j_d = (int)$j_d;

    $jy = $j_y - 979;
    $jm = $j_m - 1;
    $jd = $j_d - 1;

    $j_day_no = 365 * $jy + floor($jy / 33) * 8 + floor(($jy % 33 + 3) / 4);
    for ($i = 0; $i < $jm; ++$i) {
        $j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29];
        $j_day_no += $j_days_in_month[$i];
    }

    $j_day_no += $jd;

    $g_day_no = $j_day_no + 79;

    $gy = 1600 + 400 * floor($g_day_no / 146097);
    $g_day_no = $g_day_no % 146097;

    $leap = true;
    if ($g_day_no >= 36525) {
        $g_day_no--;
        $gy += 100 * floor($g_day_no / 36524);
        $g_day_no = $g_day_no % 36524;

        if ($g_day_no >= 365) {
            $g_day_no++;
        } else {
            $leap = false;
        }
    }

    $gy += 4 * floor($g_day_no / 1461);
    $g_day_no %= 1461;

    if ($g_day_no >= 366) {
        $leap = false;
        $g_day_no--;
        $gy += floor($g_day_no / 365);
        $g_day_no = $g_day_no % 365;
    }

    $g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    for ($i = 0; $i < 12 && $g_day_no >= $g_days_in_month[$i]; $i++) {
        if ($i == 1 && $leap) {
            $g_days_in_month[$i]++;
        }
        $g_day_no -= $g_days_in_month[$i];
    }

    $gm = $i + 1;
    $gd = $g_day_no + 1;

    return [$gy, $gm, $gd];
}

// Metabox callback to display the form and history
function acs_meta_box_callback($post) {
    wp_nonce_field('acs_meta_box_nonce_action', 'acs_meta_box_nonce_field');

    $cron_status = defined('DISABLE_WP_CRON') && DISABLE_WP_CRON ? 'غیرفعال' : 'فعال';
    $cron_message = $cron_status === 'غیرفعال' ? 'هشدار: WP-Cron غیرفعال است. برای اجرای زمان‌بندی‌ها، باید یک کرون جاب واقعی در هاست تنظیم کنید.' : 'WP-Cron فعال است. برای اطمینان از اجرای دقیق زمان‌بندی‌ها، پیشنهاد می‌شود یک کرون جاب در هاست تنظیم کنید.';
    $cron_color = $cron_status === 'غیرفعال' ? 'red' : 'green';

    $timezone = new DateTimeZone('Asia/Tehran');
    $current_time = new DateTime('now', $timezone);
    echo '<p>زمان فعلی وردپرس (به وقت تهران): ' . $current_time->format('Y-m-d H:i:s') . '</p>';
    echo '<p style="font-size: 12px; color: #555;">توسعه‌یافته توسط <a href="https://donooco.com" target="_blank">Ahmadreza Khatami (CEO of Donooco Agency)</a></p>';

    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';

    // Clean up old published comments from history
	$current_time_mysql = $current_time->format('Y-m-d H:i:s');
	$deleted = $wpdb->query(
    $wpdb->prepare(
        "DELETE FROM $table_name WHERE scheduled_time < %s AND is_published = 1 AND is_reply_published = 1 AND post_id = %d",
        $current_time_mysql,
        $post->ID
    )
	);
	if ($deleted === false) {
    	error_log('Failed to clean up old comments from history: ' . $wpdb->last_error);
	} else {
    	error_log('Cleaned up ' . $deleted . ' old comments from history for post ' . $post->ID);
	}

    $history = $wpdb->get_results($wpdb->prepare("SELECT * FROM $table_name WHERE post_id = %d ORDER BY scheduled_time DESC", $post->ID));

    if ($wpdb->last_error) {
        echo '<p style="color: red;">خطا در بازیابی هیستوری: ' . esc_html($wpdb->last_error) . '</p>';
    }

    // Get default settings
    $settings = get_option('acs_settings', [
        'reply_author' => '',
        'reply_email' => '',
        'date_time' => '',
        'tone_details' => '',
        'extra_conditions' => '',
    ]);
    ?>
    <div class="acs-metabox">
        <p style="color: <?php echo $cron_color; ?>; font-weight: bold;">
            وضعیت WP-Cron: <?php echo $cron_status; ?><br>
            <?php echo $cron_message; ?>
        </p>

        <div class="acs-accordion">
            <div class="acs-accordion-item">
                <h3 class="acs-accordion-title">زمان‌بندی دستی کامنت</h3>
                <div class="acs-accordion-content">
                    <p>
                        <label for="acs-comment-author">نام نویسنده کامنت:</label>
                        <input type="text" id="acs-comment-author" name="acs_comment_author" class="widefat">
                    </p>
                    <p>
                        <label for="acs-comment-email">ایمیل نویسنده کامنت:</label>
                        <input type="email" id="acs-comment-email" name="acs_comment_email" class="widefat">
                    </p>
                    <p>
                        <label for="acs-comment-content">متن کامنت:</label>
                        <textarea id="acs-comment-content" name="acs_comment_content" class="widefat" rows="5"></textarea>
                    </p>
                    <p>
                        <label for="acs-reply-author">نام نویسنده پاسخ:</label>
                        <input type="text" id="acs-reply-author" name="acs_reply_author" class="widefat">
                    </p>
                    <p>
                        <label for="acs-reply-email">ایمیل نویسنده پاسخ:</label>
                        <input type="email" id="acs-reply-email" name="acs_reply_email" class="widefat">
                    </p>
                    <p>
                        <label for="acs-reply-content">متن پاسخ:</label>
                        <textarea id="acs-reply-content" name="acs_reply_content" class="widefat" rows="5"></textarea>
                    </p>
                    <div class="acs-date-time-row">
                        <p class="acs-date-field">
                            <label for="acs-date">تاریخ انتشار (شمسی):</label>
                            <input type="text" id="acs-date" name="acs_date" class="widefat acs-date-picker">
                        </p>
                        <p class="acs-time-field">
                            <label for="acs-time">ساعت (HH:MM):</label>
                            <input type="text" id="acs-time" name="acs_time" placeholder="مثال: 14:30" class="widefat">
                        </p>
                    </div>
                    <p>
                        <label for="acs-minutes">یا زمان‌بندی بر اساس دقیقه (دقیقه‌های آینده):</label>
                        <input type="number" id="acs-minutes" name="acs_minutes" class="widefat" placeholder="مثال: 153">
                    </p>
                    <p id="acs-error" style="color: red; display: none;"></p>
                    <button type="button" id="acs-schedule-btn" class="button button-primary">ارسال و زمان‌بندی</button>
                    <p id="acs-success" style="color: green; display: none;">کامنت با موفقیت زمان‌بندی شد!</p>
                </div>
            </div>

            <div class="acs-accordion-item">
                <h3 class="acs-accordion-title">زمان‌بندی BULK (JSON)</h3>
                <div class="acs-accordion-content">
                    <p>
                        <label for="acs-json-text">متن JSON را اینجا کپی کنید:</label>
                        <textarea id="acs-json-text" name="acs_json_text" class="widefat" rows="10" placeholder='مثال: [{"name": "علی رضایی", "question": "این چیه؟", "answer": "یه محصول جدیده.", "date": "1404/01/20", "time": "14:30", "comment_email": "ali.rezaei@example.com", "reply_author": "پاسخ‌دهنده ۱", "reply_email": "reply1@example.com", "ip_address": "5.200.123.45"}]'></textarea>
                    </p>
                    <button type="button" id="acs-json-schedule-btn" class="button button-primary">زمان‌بندی از JSON</button>
                    <p id="acs-json-error" style="color: red; display: none;"></p>
                    <p id="acs-json-success" style="color: green; display: none;"></p>

                    <h3>تولید پرامپت برای هوش مصنوعی</h3>
                    <p>اگر می‌خواهید پرامپت شما به صورت خودکار و صحیح توسط افزونه آماده شود، کافی است فرم زیر را پر کنید و دکمه "تولید پرامپت" را بزنید. همچنین می‌توانید پرامپت خود را به صورت دستی بنویسید و خروجی را در بخش JSON بالا قرار دهید.</p>
                    <form id="acs-generate-prompt-form">
                        <div class="acs-reply-author-email-row">
                            <p class="acs-reply-author-field">
                                <label for="acs-prompt-reply-author">نام پاسخ‌دهنده:</label><br>
                                <input type="text" id="acs-prompt-reply-author" name="reply_author" class="widefat" value="<?php echo esc_attr($settings['reply_author']); ?>">
                            </p>
                            <p class="acs-reply-email-field">
                                <label for="acs-prompt-reply-email">ایمیل پاسخ‌دهنده:</label><br>
                                <input type="email" id="acs-prompt-reply-email" name="reply_email" class="widefat" value="<?php echo esc_attr($settings['reply_email']); ?>">
                            </p>
                        </div>
                        <p>
                            <label for="acs-date-time">پرامپت تاریخ و زمان و تعداد کامنت مورد نیاز:</label><br>
                            <textarea id="acs-date-time" name="date_time" class="widefat" rows="5" placeholder="به طور مثال: به مدت 30 روز از تاریخ 22 اردیبهشت 1404 شروع کن و هر روز یه کامنت بزار ولی ساعتش به صورت رندوم دست خودت باشه (بین 9 صبح تا 12 شب)"><?php echo esc_textarea($settings['date_time']); ?></textarea>
                        </p>
                        <p>
                            <label for="acs-tone-details">توضیحات لحن و موارد رعایت شده در کامنت‌ها:</label><br>
                            <textarea id="acs-tone-details" name="tone_details" class="widefat" rows="5" placeholder="مثلا: لحن سوالات دوستانه و محاوره‌ای باشه اما پاسخ‌ها علمی و پر محتوا باشه"><?php echo esc_textarea($settings['tone_details']); ?></textarea>
                        </p>
                        <p>
                            <label for="acs-extra-conditions">شرایط اضافی (اختیاری):</label><br>
                            <textarea id="acs-extra-conditions" name="extra_conditions" class="widefat" rows="5" placeholder="مثلا: شرایط ارسال برای تهران 1 الی دو روز کاری و شهرستان 2 الی 3 روز کاری هست همینطور حواست باشه که ما تخفیف نداریم و تمام محصولاتمون اورجینال هست روی این تاکید داشته باش همیشه"><?php echo esc_textarea($settings['extra_conditions']); ?></textarea>
                        </p>
                        <button type="button" id="acs-generate-prompt-btn" class="button button-primary">تولید پرامپت آماده برای هوش مصنوعی</button>
                    </form>
                    <div id="acs-prompt-result" style="margin-top: 20px;"></div>
                    <div id="acs-copy-prompt-container" style="margin-top: 10px; display: none;">
                        <button type="button" id="acs-copy-prompt-btn" class="button button-secondary">کپی پرامپت در کلیپ‌بورد</button>
                        <p id="acs-copy-prompt-message" style="color: green; display: none; margin-top: 5px;">پرامپت تو کلیپ‌بوردته!</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="acs-history">
            <h3>تاریخچه کامنت‌های زمان‌بندی‌شده</h3>
            <?php if (empty($history)) : ?>
                <p>هیچ کامنت زمان‌بندی‌شده‌ای وجود ندارد.</p>
            <?php else : ?>
                <div class="acs-history-actions">
                    <button type="button" id="acs-bulk-delete-btn" class="button button-danger" style="display: none;">حذف انتخاب‌شده‌ها</button>
                </div>
                <ul class="acs-history-list">
                    <?php foreach ($history as $item) : ?>
                        <?php
                        $datetime = new DateTime($item->scheduled_time, new DateTimeZone('UTC'));
                        $datetime->setTimezone(new DateTimeZone('Asia/Tehran'));
                        list($g_y, $g_m, $g_d) = explode('-', $datetime->format('Y-m-d'));
                        list($hour, $minute) = explode(':', $datetime->format('H:i'));
                        list($j_y, $j_m, $j_d) = gregorian_to_jalali($g_y, $g_m, $g_d);
                        $jalali_date = sprintf('%d/%02d/%02d %02d:%02d', $j_y, $j_m, $j_d, $hour, $minute);
                        ?>
                        <li class="acs-history-item" data-id="<?php echo esc_attr($item->id); ?>" data-transient-key="<?php echo esc_attr($item->transient_key); ?>">
                            <div class="acs-history-summary">
                                <input type="checkbox" class="acs-history-checkbox" />
                                <span class="acs-history-author"><?php echo esc_html($item->comment_author); ?></span> - 
                                <span class="acs-history-date"><?php echo esc_html($jalali_date); ?></span>
                                <span class="acs-history-toggle"> (نمایش جزئیات)</span>
                                <div class="acs-history-actions-buttons">
                                    <button class="acs-edit-btn" title="ویرایش کامنت"><i class="fa fa-edit"></i></button>
                                    <button class="acs-delete-btn" title="حذف کامنت"><i class="fa fa-trash"></i></button>
                                </div>
                            </div>
                            <div class="acs-history-details">
                                <p><strong>ایمیل کامنت‌دهنده:</strong> <?php echo esc_html($item->comment_email); ?></p>
                                <p><strong>متن کامنت:</strong> <?php echo esc_html($item->comment_content); ?></p>
                                <p><strong>نام نویسنده پاسخ:</strong> <?php echo esc_html($item->reply_author); ?></p>
                                <p><strong>ایمیل پاسخ‌دهنده:</strong> <?php echo esc_html($item->reply_email); ?></p>
                                <p><strong>متن پاسخ:</strong> <?php echo esc_html($item->reply_content); ?></p>
                                <p><strong>آی‌پی:</strong> <?php echo esc_html($item->ip_address ? $item->ip_address : 'نامشخص'); ?></p>
                            </div>
                        </li>
                    <?php endforeach; ?>
                </ul>
            <?php endif; ?>
        </div>

        <div id="acs-edit-form" style="display: none; margin-top: 20px;">
            <h3>ویرایش کامنت</h3>
            <form id="acs-edit-comment-form">
                <input type="hidden" id="edit-comment-id" name="comment_id">
                <input type="hidden" id="edit-transient-key" name="transient_key">
                <p>
                    <label for="edit-comment-author">نام نویسنده کامنت:</label><br>
                    <input type="text" id="edit-comment-author" name="comment_author" class="widefat">
                </p>
                <p>
                    <label for="edit-comment-email">ایمیل نویسنده کامنت:</label><br>
                    <input type="email" id="edit-comment-email" name="comment_email" class="widefat">
                </p>
                <p>
                    <label for="edit-comment-content">متن کامنت:</label><br>
                    <textarea id="edit-comment-content" name="comment_content" class="widefat" rows="5"></textarea>
                </p>
                <p>
                    <label for="edit-reply-author">نام نویسنده پاسخ:</label><br>
                    <input type="text" id="edit-reply-author" name="reply_author" class="widefat">
                </p>
                <p>
                    <label for="edit-reply-email">ایمیل نویسنده پاسخ:</label><br>
                    <input type="email" id="edit-reply-email" name="reply_email" class="widefat">
                </p>
                <p>
                    <label for="edit-reply-content">متن پاسخ:</label><br>
                    <textarea id="edit-reply-content" name="reply_content" class="widefat" rows="5"></textarea>
                </p>
                <div class="acs-date-time-row">
                    <p class="acs-date-field">
                        <label for="edit-date">تاریخ انتشار (شمسی):</label><br>
                        <input type="text" id="edit-date" name="date" class="widefat acs-date-picker">
                    </p>
                    <p class="acs-time-field">
                        <label for="edit-time">ساعت (HH:MM):</label><br>
                        <input type="text" id="edit-time" name="time" class="widefat">
                    </p>
                </div>
                <p>
                    <label for="edit-ip-address">آی‌پی:</label><br>
                    <input type="text" id="edit-ip-address" name="ip_address" class="widefat">
                </p>
                <button type="button" id="acs-save-edit-btn" class="button button-primary">ذخیره تغییرات</button>
                <button type="button" id="acs-cancel-edit-btn" class="button">لغو</button>
            </form>
        </div>
    </div>
    <?php
}

// Function to generate a random email for the comment author (fallback)
function acs_generate_random_email() {
    $first_names = ['ali', 'sara', 'reza', 'maryam', 'mehdi', 'narges'];
    $last_names = ['ahmadi', 'mohammadi', 'rezai', 'khatami', 'shariati', 'ghasemi'];
    $domains = ['gmail.com', 'yahoo.com', 'hotmail.com'];

    $first_name = $first_names[array_rand($first_names)];
    $last_name = $last_names[array_rand($last_names)];
    $domain = $domains[array_rand($domains)];

    return $first_name . '.' . $last_name . '@' . $domain;
}

// Function to get data from custom transients table
function acs_get_transient($transient_key) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_transients';

    $row = $wpdb->get_row(
        $wpdb->prepare(
            "SELECT transient_value, expiration FROM $table_name WHERE transient_key = %s",
            $transient_key
        )
    );

    if (!$row) {
        error_log('Transient not found: ' . $transient_key);
        return false;
    }

    // Check expiration
    if ($row->expiration < time()) {
        // Delete expired data
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        error_log('Transient expired and deleted: ' . $transient_key);
        return false;
    }

    return maybe_unserialize($row->transient_value);
}

// Function to set data in custom transients table
function acs_set_transient($transient_key, $value, $expiration) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_transients';

    $serialized_value = maybe_serialize($value);

    $result = $wpdb->replace(
        $table_name,
        [
            'transient_key' => $transient_key,
            'transient_value' => $serialized_value,
            'expiration' => $expiration,
        ],
        ['%s', '%s', '%d']
    );

    if ($result === false) {
        error_log('Failed to set transient ' . $transient_key . ': ' . $wpdb->last_error);
        return false;
    }

    return true;
}

// AJAX handler to save the scheduled comment
add_action('wp_ajax_acs_save_comment', 'acs_save_comment');
function acs_save_comment() {
    error_log('acs_save_comment started');

    if (!check_ajax_referer('acs_meta_box_nonce_action', 'nonce', false)) {
        error_log('Nonce verification failed');
        wp_send_json_error('خطا در اعتبارسنجی nonce');
    }

    if (!current_user_can('manage_options')) {
        error_log('User does not have permission');
        wp_send_json_error('دسترسی غیرمجاز');
    }

    $post_id = isset($_POST['post_id']) ? intval($_POST['post_id']) : 0;
    $comment_author = isset($_POST['comment_author']) ? sanitize_text_field($_POST['comment_author']) : '';
    $comment_email = isset($_POST['comment_email']) ? sanitize_email($_POST['comment_email']) : acs_generate_random_email();
    $comment_content = isset($_POST['comment_content']) ? sanitize_textarea_field($_POST['comment_content']) : '';
    $reply_author = isset($_POST['reply_author']) ? sanitize_text_field($_POST['reply_author']) : '';
    $reply_email = isset($_POST['reply_email']) ? sanitize_email($_POST['reply_email']) : '';
    $reply_content = isset($_POST['reply_content']) ? sanitize_textarea_field($_POST['reply_content']) : '';
    $date = isset($_POST['date']) ? sanitize_text_field($_POST['date']) : '';
    $time = isset($_POST['time']) ? sanitize_text_field($_POST['time']) : '';
    $minutes = isset($_POST['minutes']) ? sanitize_text_field($_POST['minutes']) : '';

    $current_user = wp_get_current_user();
    $reply_email = !empty($reply_email) ? $reply_email : $current_user->user_email;

    error_log('Input data - post_id: ' . $post_id);
    error_log('Input data - comment_author: ' . $comment_author);
    error_log('Input data - comment_email: ' . $comment_email);
    error_log('Input data - comment_content: ' . $comment_content);
    error_log('Input data - reply_author: ' . $reply_author);
    error_log('Input data - reply_email: ' . $reply_email);
    error_log('Input data - reply_content: ' . $reply_content);
    error_log('Input data - date: ' . $date);
    error_log('Input data - time: ' . $time);
    error_log('Input data - minutes: ' . $minutes);

    $data = [
        'post_id' => $post_id,
        'comment_author' => $comment_author,
        'comment_email' => $comment_email,
        'comment_content' => $comment_content,
        'reply_author' => $reply_author,
        'reply_email' => $reply_email,
        'reply_content' => $reply_content,
        'date' => $date,
        'time' => $time,
        'minutes' => $minutes
    ];

    error_log('Calling acs_save_comment_internal with data: ' . print_r($data, true));
    $response = acs_save_comment_internal($data);
    error_log('acs_save_comment_internal response: ' . print_r($response, true));

    if (!$response['success']) {
        error_log('acs_save_comment failed: ' . print_r($response['message'], true));
        wp_send_json_error($response['message']);
    }

    wp_send_json_success($response['message']);
}

// AJAX handler to process JSON text
add_action('wp_ajax_acs_process_json', 'acs_process_json');
function acs_process_json() {
    if (!check_ajax_referer('acs_meta_box_nonce_action', 'nonce', false)) {
        error_log('Nonce verification failed');
        wp_send_json_error('خطا در اعتبارسنجی nonce');
    }

    if (!current_user_can('manage_options')) {
        error_log('User does not have permission');
        wp_send_json_error('دسترسی غیرمجاز');
    }

    if (!isset($_POST['json_text']) || empty(trim($_POST['json_text']))) {
        error_log('No JSON text provided');
        wp_send_json_error('لطفاً متن JSON را وارد کنید');
    }

    $json_text = stripslashes($_POST['json_text']);
    $json_text = trim($json_text);
    error_log('Raw JSON Text: ' . $json_text);
    $comments = json_decode($json_text, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log('Invalid JSON format: ' . json_last_error_msg());
        wp_send_json_error('فرمت JSON نامعتبر است: ' . json_last_error_msg());
    }

    if (empty($comments) || !is_array($comments)) {
        error_log('No comments found in JSON');
        wp_send_json_error('هیچ کامنتی در متن JSON یافت نشد');
    }

    $post_id = isset($_POST['post_id']) ? intval($_POST['post_id']) : 0;
    if (empty($post_id)) {
        error_log('Invalid post ID');
        wp_send_json_error('شناسه پست نامعتبر است');
    }

    $errors = [];
    $success_count = 0;

    foreach ($comments as $index => $comment) {
        if (!isset($comment['name']) || !isset($comment['question']) || !isset($comment['answer']) ||
            !isset($comment['date']) || !isset($comment['time']) || !isset($comment['comment_email']) ||
            !isset($comment['reply_author']) || !isset($comment['reply_email']) || !isset($comment['ip_address'])) {
            $errors[] = "کامنت شماره " . ($index + 1) . ": اطلاعات ناقص است";
            continue;
        }

        $data = [
            'post_id' => $post_id,
            'comment_author' => sanitize_text_field($comment['name']),
            'comment_email' => sanitize_email($comment['comment_email']),
            'comment_content' => sanitize_textarea_field($comment['question']),
            'reply_author' => sanitize_text_field($comment['reply_author']),
            'reply_email' => sanitize_email($comment['reply_email']),
            'reply_content' => sanitize_textarea_field($comment['answer']),
            'date' => sanitize_text_field($comment['date']),
            'time' => sanitize_text_field($comment['time']),
            'minutes' => ''
        ];

        $response = acs_save_comment_internal($data, $comment['ip_address']);

        if (!$response['success']) {
            $error_message = is_string($response['message']) ? $response['message'] : 'خطا در زمان‌بندی';
            $errors[] = "کامنت شماره " . ($index + 1) . ": " . $error_message;
        } else {
            $success_count++;
        }
    }

    if (!empty($errors)) {
        wp_send_json_error(implode('<br>', $errors));
    }

    wp_send_json_success("تعداد $success_count کامنت با موفقیت زمان‌بندی شد!");
}

// Internal function to save comment data
function acs_save_comment_internal($data, $ip_address = '') {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $transient_table = $wpdb->prefix . 'acs_transients';

    // Extract data
    $post_id = $data['post_id'];
    $comment_author = $data['comment_author'];
    $comment_email = $data['comment_email'];
    $comment_content = $data['comment_content'];
    $reply_author = $data['reply_author'];
    $reply_email = $data['reply_email'];
    $reply_content = $data['reply_content'];
    $date = $data['date'];
    $time = $data['time'];
    $minutes = $data['minutes'];

    // Validate required fields
    $missing_fields = [];
    if (empty($post_id)) $missing_fields[] = 'شناسه پست';
    if (empty($comment_author)) $missing_fields[] = 'نام نویسنده کامنت';
    if (empty($comment_email)) $missing_fields[] = 'ایمیل نویسنده کامنت';
    if (empty($comment_content)) $missing_fields[] = 'متن کامنت';
    if (empty($reply_author)) $missing_fields[] = 'نام نویسنده پاسخ';
    if (empty($reply_email)) $missing_fields[] = 'ایمیل نویسنده پاسخ';
    if (empty($reply_content)) $missing_fields[] = 'متن پاسخ';

    if (!empty($missing_fields)) {
        $message = 'لطفاً اطلاعات زیر را کامل کنید: ' . implode('، ', $missing_fields);
        error_log('Validation failed: ' . $message);
        return [
            'success' => false,
            'message' => $message
        ];
    }

    // Check if both date/time and minutes are filled
    $date_time_filled = !empty($date) && !empty($time);
    $minutes_filled = $minutes !== '' && is_numeric($minutes) && (int)$minutes > 0;

    if ($date_time_filled && $minutes_filled) {
        return [
            'success' => false,
            'message' => 'لطفاً فقط یکی از تاریخ/ساعت یا زمان‌بندی بر اساس دقیقه را پر کنید'
        ];
    }

    if (!$date_time_filled && !$minutes_filled) {
        return [
            'success' => false,
            'message' => 'لطفاً تاریخ و ساعت یا زمان‌بندی بر اساس دقیقه را وارد کنید'
        ];
    }

    // Calculate timestamp
    $timezone = new DateTimeZone('Asia/Tehran');
    $now = new DateTime('now', $timezone);
    $current_timestamp = $now->getTimestamp();

    if ($date_time_filled) {
        // Validate time format (HH:MM)
        if (!preg_match('/^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$/', $time)) {
            return [
                'success' => false,
                'message' => 'فرمت ساعت نامعتبر است. لطفاً از فرمت HH:MM استفاده کنید (مثال: 14:30)'
            ];
        }

        // Validate date format (YYYY/MM/DD)
        $date_parts = explode('/', $date);
        if (count($date_parts) !== 3) {
            return [
                'success' => false,
                'message' => 'فرمت تاریخ نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید (مثال: 1404/01/20)'
            ];
        }
        list($year, $month, $day) = $date_parts;
        $month = str_pad($month, 2, '0', STR_PAD_LEFT);
        $day = str_pad($day, 2, '0', STR_PAD_LEFT);
        $date = "$year/$month/$day";

        if (!preg_match('/^\d{4}\/\d{2}\/\d{2}$/', $date)) {
            return [
                'success' => false,
                'message' => 'فرمت تاریخ نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید (مثال: 1404/01/20)'
            ];
        }

        // Convert Jalali to Gregorian
        list($year, $month, $day) = array_map('intval', explode('/', $date));
        $gregorian_date = jalali_to_gregorian($year, $month, $day);
        if (!$gregorian_date || count($gregorian_date) !== 3) {
            error_log('Failed to convert Persian date to Gregorian: Year=' . $year . ', Month=' . $month . ', Day=' . $day);
            return [
                'success' => false,
                'message' => 'خطا در تبدیل تاریخ شمسی به میلادی'
            ];
        }

        list($hour, $minute) = array_map('intval', explode(':', $time));
        try {
            $datetime = new DateTime("{$gregorian_date[0]}-{$gregorian_date[1]}-{$gregorian_date[2]} {$hour}:{$minute}:00", $timezone);
            $timestamp = $datetime->getTimestamp();
            error_log('Scheduled timestamp from date/time: ' . $timestamp . ' (' . $datetime->format('Y-m-d H:i:s') . ')');
        } catch (Exception $e) {
            error_log('Failed to create DateTime object: ' . $e->getMessage());
            return [
                'success' => false,
                'message' => 'خطا در پردازش تاریخ و زمان: ' . $e->getMessage()
            ];
        }

        // Ensure timestamp is in the future
        if ($timestamp <= $current_timestamp) {
            return [
                'success' => false,
                'message' => 'تاریخ و زمان انتخاب‌شده گذشته است. لطفاً زمان آینده‌ای انتخاب کنید.'
            ];
        }
    } else {
        $minutes = (int)$minutes;
        $timestamp = $current_timestamp + ($minutes * 60);
        error_log('Calculated timestamp for ' . $minutes . ' minutes from now: ' . $timestamp . ' (' . $now->format('Y-m-d H:i:s') . ' + ' . ($minutes * 60) . ' seconds)');

        // Ensure timestamp is in the future
        if ($timestamp <= $current_timestamp) {
            return [
                'success' => false,
                'message' => 'زمان انتخاب‌شده گذشته است. لطفاً تعداد دقیقه‌های بیشتری انتخاب کنید.'
            ];
        }
    }

    // Prepare comment data
    $comment_data = [
        'post_id' => $post_id,
        'comment_author' => $comment_author,
        'comment_email' => $comment_email,
        'comment_content' => $comment_content,
        'reply_author' => $reply_author,
        'reply_email' => $reply_email,
        'reply_content' => $reply_content,
        'timestamp' => $timestamp
    ];

    // Generate transient key
    $transient_key = 'acs_comment_' . md5(serialize($comment_data) . time());
    $expiration = $timestamp + (7 * DAY_IN_SECONDS); // Transient expires 7 days after scheduled time

    // Save to custom transients table
    if (!acs_set_transient($transient_key, $comment_data, $expiration)) {
        return [
            'success' => false,
            'message' => 'خطا در ذخیره‌سازی موقت داده‌ها'
        ];
    }

    // Save to history table
    $scheduled_time = date('Y-m-d H:i:s', $timestamp);
    error_log('Attempting to insert into history table: ' . print_r([
        'post_id' => $post_id,
        'comment_author' => $comment_author,
        'comment_email' => $comment_email,
        'comment_content' => $comment_content,
        'reply_author' => $reply_author,
        'reply_email' => $reply_email,
        'reply_content' => $reply_content,
        'scheduled_time' => $scheduled_time,
        'transient_key' => $transient_key,
        'ip_address' => $ip_address,
        'is_published' => 0
    ], true));

    $result = $wpdb->insert(
        $table_name,
        [
            'post_id' => $post_id,
            'comment_author' => $comment_author,
            'comment_email' => $comment_email,
            'comment_content' => $comment_content,
            'reply_author' => $reply_author,
            'reply_email' => $reply_email,
            'reply_content' => $reply_content,
            'scheduled_time' => $scheduled_time,
            'transient_key' => $transient_key,
            'ip_address' => $ip_address,
            'is_published' => 0
        ],
        ['%d', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%d']
    );

    if ($result === false) {
        error_log('Failed to insert into history table: ' . $wpdb->last_error);
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
        return [
            'success' => false,
            'message' => 'خطا در ذخیره‌سازی در جدول تاریخچه: ' . $wpdb->last_error
        ];
    }
    error_log('Successfully inserted into history table with ID: ' . $wpdb->insert_id);

    // Schedule the comment publishing
    if (!wp_schedule_single_event($timestamp, 'acs_publish_comment', [$transient_key])) {
        error_log('Failed to schedule comment publishing for transient: ' . $transient_key);
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
        return [
            'success' => false,
            'message' => 'خطا در زمان‌بندی انتشار کامنت'
        ];
    }

    // Check Developer Mode for reply delay
    $settings = get_option('acs_settings', ['developer_mode' => 0, 'reply_delay_minutes' => 10]);
    $reply_delay_minutes = $settings['developer_mode'] ? (int)$settings['reply_delay_minutes'] : 10;
    $reply_delay_minutes = max(1, $reply_delay_minutes); // Minimum 1 minute to ensure proper scheduling

    // Set reply timestamp based on settings
    $reply_timestamp = $timestamp + ($reply_delay_minutes * 60);
    $now = new DateTime('now', $timezone);
    $current_timestamp = $now->getTimestamp();

    // Ensure reply is scheduled in the future
    if ($reply_timestamp <= $current_timestamp) {
        $reply_timestamp = $current_timestamp + ($reply_delay_minutes * 60);
        error_log('Adjusted reply timestamp to ' . $reply_timestamp . ' because it was in the past');
    }

    // Schedule the reply publishing
    if (!wp_schedule_single_event($reply_timestamp, 'acs_publish_reply', [$transient_key])) {
        error_log('Failed to schedule reply publishing for transient: ' . $transient_key);
        wp_clear_scheduled_hook('acs_publish_comment', [$transient_key]);
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
        return [
            'success' => false,
            'message' => 'خطا در زمان‌بندی انتشار پاسخ'
        ];
    }

    // Verify the schedules
    $scheduled_comment = wp_get_scheduled_event('acs_publish_comment', [$transient_key]);
    $scheduled_reply = wp_get_scheduled_event('acs_publish_reply', [$transient_key]);
    if (!$scheduled_comment || !$scheduled_reply) {
        error_log('Scheduled events not found after scheduling for transient: ' . $transient_key);
        wp_clear_scheduled_hook('acs_publish_comment', [$transient_key]);
        wp_clear_scheduled_hook('acs_publish_reply', [$transient_key]);
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
        return [
            'success' => false,
            'message' => 'خطا در تأیید زمان‌بندی وظایف'
        ];
    }

    error_log('Successfully scheduled comment and reply for transient: ' . $transient_key . ' at ' . date('Y-m-d H:i:s', $timestamp) . ' and ' . date('Y-m-d H:i:s', $reply_timestamp));
    return [
        'success' => true,
        'message' => 'کامنت با موفقیت زمان‌بندی شد'
    ];
}

// AJAX handler to delete a scheduled comment
add_action('wp_ajax_acs_delete_comment', 'acs_delete_comment');
function acs_delete_comment() {
    if (!check_ajax_referer('acs_meta_box_nonce_action', 'nonce', false)) {
        error_log('Nonce verification failed');
        wp_send_json_error('خطا در اعتبارسنجی nonce');
    }

    if (!current_user_can('manage_options')) {
        error_log('User does not have permission');
        wp_send_json_error('دسترسی غیرمجاز');
    }

    $comment_ids = isset($_POST['comment_ids']) ? array_map('intval', (array)$_POST['comment_ids']) : [];
    $transient_keys = isset($_POST['transient_keys']) ? array_map('sanitize_text_field', (array)$_POST['transient_keys']) : [];

    if (empty($comment_ids) || empty($transient_keys) || count($comment_ids) !== count($transient_keys)) {
        error_log('Invalid comment IDs or transient keys');
        wp_send_json_error('شناسه‌های کامنت یا کلیدهای transient نامعتبر هستند');
    }

    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $transient_table = $wpdb->prefix . 'acs_transients';
    $errors = [];

    for ($i = 0; $i < count($comment_ids); $i++) {
        $comment_id = $comment_ids[$i];
        $transient_key = $transient_keys[$i];

        // Clear scheduled events
        wp_clear_scheduled_hook('acs_publish_comment', [$transient_key]);
        wp_clear_scheduled_hook('acs_publish_reply', [$transient_key]);

        // Delete from custom transients table
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);

        // Delete from history table
        $deleted = $wpdb->delete($table_name, ['id' => $comment_id], ['%d']);
        if ($deleted === false) {
            $errors[] = "خطا در حذف کامنت با شناسه $comment_id: " . $wpdb->last_error;
        }
    }

    if (!empty($errors)) {
        error_log('Errors during bulk delete: ' . implode(', ', $errors));
        wp_send_json_error(implode('<br>', $errors));
    }

    wp_send_json_success('کامنت‌ها با موفقیت حذف شدند');
}

// AJAX handler to get comment data for editing
add_action('wp_ajax_acs_get_comment', 'acs_get_comment_callback');
function acs_get_comment_callback() {
    check_ajax_referer('acs_get_comment_nonce', 'nonce');

    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $comment_id = intval($_POST['comment_id']);

    $comment = $wpdb->get_row($wpdb->prepare("SELECT * FROM $table_name WHERE id = %d", $comment_id));

    if (!$comment) {
        wp_send_json_error('کامنت یافت نشد');
    }

    $datetime = new DateTime($comment->scheduled_time, new DateTimeZone('UTC'));
    $datetime->setTimezone(new DateTimeZone('Asia/Tehran'));
    list($g_y, $g_m, $g_d) = explode('-', $datetime->format('Y-m-d'));
    list($hour, $minute) = explode(':', $datetime->format('H:i'));
    list($j_y, $j_m, $j_d) = gregorian_to_jalali($g_y, $g_m, $g_d);
    $jalali_date = sprintf('%d/%02d/%02d', $j_y, $j_m, $j_d);
    $time = sprintf('%02d:%02d', $hour, $minute);

    wp_send_json_success([
        'transient_key' => $comment->transient_key,
        'comment_author' => $comment->comment_author,
        'comment_email' => $comment->comment_email,
        'comment_content' => $comment->comment_content,
        'reply_author' => $comment->reply_author,
        'reply_email' => $comment->reply_email,
        'reply_content' => $comment->reply_content,
        'date' => $jalali_date,
        'time' => $time,
        'ip_address' => $comment->ip_address,
    ]);
}

// AJAX handler to update a scheduled comment
add_action('wp_ajax_acs_update_comment', 'acs_update_comment_callback');
function acs_update_comment_callback() {
    check_ajax_referer('acs_update_comment_nonce', 'nonce');

    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $transient_table = $wpdb->prefix . 'acs_transients';
    $comment_id = intval($_POST['comment_id']);
    $transient_key = sanitize_text_field($_POST['transient_key']);
    $comment_author = sanitize_text_field($_POST['comment_author']);
    $comment_email = sanitize_email($_POST['comment_email']);
    $comment_content = sanitize_textarea_field($_POST['comment_content']);
    $reply_author = sanitize_text_field($_POST['reply_author']);
    $reply_email = sanitize_email($_POST['reply_email']);
    $reply_content = sanitize_textarea_field($_POST['reply_content']);
    $date = sanitize_text_field($_POST['date']);
    $time = sanitize_text_field($_POST['time']);
    $ip_address = sanitize_text_field($_POST['ip_address']);
    $post_id = intval($_POST['post_id']);

    $missing_fields = [];
    if (empty($comment_author)) $missing_fields[] = 'نام نویسنده کامنت';
    if (empty($comment_email)) $missing_fields[] = 'ایمیل نویسنده کامنت';
    if (empty($comment_content)) $missing_fields[] = 'متن کامنت';
    if (empty($reply_author)) $missing_fields[] = 'نام نویسنده پاسخ';
    if (empty($reply_email)) $missing_fields[] = 'ایمیل نویسنده پاسخ';
    if (empty($reply_content)) $missing_fields[] = 'متن پاسخ';
    if (empty($date)) $missing_fields[] = 'تاریخ';
    if (empty($time)) $missing_fields[] = 'ساعت';

    if (!empty($missing_fields)) {
        wp_send_json_error('لطفاً اطلاعات زیر را کامل کنید: ' . implode('، ', $missing_fields));
    }

    if (!preg_match('/^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$/', $time)) {
        wp_send_json_error('فرمت ساعت نامعتبر است. لطفاً از فرمت HH:MM استفاده کنید (مثال: 14:30)');
    }

    if (!preg_match('/^\d{4}\/\d{2}\/\d{2}$/', $date)) {
        wp_send_json_error('فرمت تاریخ نامعتبر است. لطفاً از فرمت YYYY/MM/DD استفاده کنید (مثال: 1404/01/20)');
    }

    list($year, $month, $day) = explode('/', $date);
    $gregorian_date = jalali_to_gregorian($year, $month, $day);
    if (!$gregorian_date || count($gregorian_date) !== 3) {
        wp_send_json_error('خطا در تبدیل تاریخ شمسی به میلادی');
    }

    list($hour, $minute) = explode(':', $time);

    try {
        $datetime = new DateTime("{$gregorian_date[0]}-{$gregorian_date[1]}-{$gregorian_date[2]} {$hour}:{$minute}:00", new DateTimeZone('Asia/Tehran'));
        $timestamp = $datetime->getTimestamp();
    } catch (Exception $e) {
        wp_send_json_error('خطا در پردازش تاریخ و زمان: ' . $e->getMessage());
    }

    $timezone = new DateTimeZone('Asia/Tehran');
    $now = new DateTime('now', $timezone);
    $current_timestamp = $now->getTimestamp();

    if ($timestamp < $current_timestamp) {
        wp_send_json_error('تاریخ و زمان انتخاب‌شده گذشته است');
    }

    $comment_data = [
        'post_id' => $post_id,
        'comment_author' => $comment_author,
        'comment_email' => $comment_email,
        'comment_content' => $comment_content,
        'reply_author' => $reply_author,
        'reply_email' => $reply_email,
        'reply_content' => $reply_content,
        'timestamp' => $timestamp
    ];

    // Update custom transient
    $expiration = $timestamp + (7 * DAY_IN_SECONDS); // Transient expires 7 days after scheduled time
    if (!acs_set_transient($transient_key, $comment_data, $expiration)) {
        wp_send_json_error('خطا در به‌روزرسانی داده‌های موقت');
    }

    $updated = $wpdb->update(
        $table_name,
        [
            'comment_author' => $comment_author,
            'comment_email' => $comment_email,
            'comment_content' => $comment_content,
            'reply_author' => $reply_author,
            'reply_email' => $reply_email,
            'reply_content' => $reply_content,
            'scheduled_time' => date('Y-m-d H:i:s', $timestamp),
            'ip_address' => $ip_address,
        ],
        ['id' => $comment_id],
        ['%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'],
        ['%d']
    );

    if ($updated === false) {
        error_log('Failed to update history record: ' . $wpdb->last_error);
        wp_send_json_error('خطا در به‌روزرسانی جدول تاریخچه: ' . $wpdb->last_error);
    }

    // Clear previous schedules
    wp_clear_scheduled_hook('acs_publish_comment', [$transient_key]);
    wp_clear_scheduled_hook('acs_publish_reply', [$transient_key]);

    // Reschedule events
    if (!wp_schedule_single_event($timestamp, 'acs_publish_comment', [$transient_key])) {
        wp_send_json_error('خطا در زمان‌بندی مجدد انتشار کامنت');
    }
    if (!wp_schedule_single_event($timestamp + 600, 'acs_publish_reply', [$transient_key])) {
        wp_clear_scheduled_hook('acs_publish_comment', [$transient_key]);
        wp_send_json_error('خطا در زمان‌بندی مجدد انتشار پاسخ');
    }

    wp_send_json_success('کامنت با موفقیت به‌روزرسانی شد');
}

// AJAX handler to generate prompt
add_action('wp_ajax_acs_generate_prompt', 'acs_generate_prompt_callback');
function acs_generate_prompt_callback() {
    check_ajax_referer('acs_generate_prompt_nonce', 'nonce');

    $post_id = isset($_POST['post_ID']) ? intval($_POST['post_ID']) : 0;
    $reply_author = isset($_POST['reply_author']) ? sanitize_text_field($_POST['reply_author']) : '';
    $reply_email = isset($_POST['reply_email']) ? sanitize_email($_POST['reply_email']) : '';
    $date_time = isset($_POST['date_time']) ? sanitize_textarea_field($_POST['date_time']) : '';
    $tone_details = isset($_POST['tone_details']) ? sanitize_textarea_field($_POST['tone_details']) : '';
    $extra_conditions = isset($_POST['extra_conditions']) ? sanitize_textarea_field($_POST['extra_conditions']) : '';

    if (!$post_id || !$reply_author || !$reply_email || !$date_time || !$tone_details) {
        wp_send_json_error('لطفاً تمام فیلدهای الزامی را پر کنید');
    }

    $page_url = get_permalink($post_id);
    if (!$page_url) {
        wp_send_json_error('خطا در بازیابی لینک صفحه');
    }

    // Get today's date in Jalali (Persian) format
    $timezone = new DateTimeZone('Asia/Tehran');
    $today = new DateTime('now', $timezone);
    list($g_year, $g_month, $g_day) = explode('-', $today->format('Y-m-d'));
    list($j_year, $j_month, $j_day) = gregorian_to_jalali($g_year, $g_month, $g_day);
    $jalali_today = sprintf('%d/%02d/%02d', $j_year, $j_month, $j_day);

    $prompt = "سلام! می‌خوام برای این صفحه: $page_url\n\n";
    $prompt .= "کامنت با سوال و جواب بنویسی که به صورت json استاندارد باشه و برام بفرستی.\n\n";
    $prompt .= "**جزئیات کامنت‌ها:**\n";
    $prompt .= "- **نام کامنت‌دهنده:** به صورت رندوم اسم‌های ایرانی انتخاب کن\n";
    $prompt .= "- **ایمیل کامنت‌دهنده:** به صورت رندوم جیمیل ایرانی بساز (مثل ali.rezaei@gmail.com).\n";
    $prompt .= "- **شرایط سوال و پاسخ ها:** سوالات درباره مطلب صفحه و یا مرتبط به مطلب صفحه باشه. $tone_details\n";
    $prompt .= "- **نام پاسخ‌دهنده:** همیشه بنویس \"$reply_author\".\n";
    $prompt .= "- **ایمیل پاسخ‌دهنده:** همیشه بنویس \"$reply_email\".\n";
    $prompt .= "- **شرایط اضافی و نکات:** $extra_conditions\n";
    $prompt .= "- **شروع تاریخ کامنت اول:** $jalali_today\n";
    $prompt .= "- **تاریخ و ساعت:** $date_time (به فرمت YYYY/MM/DD) و دقت کن که تاریخ ها همگی شمسی باشه.\n";
    $prompt .= "- **آی‌پی کامنت‌دهنده:** برای هر کامنت، یه آی‌پی رندوم ایرانی تولید کن (مثلاً توی رنج 5.200.0.0 تا 5.202.255.255، یا 185.88.0.0 تا 185.88.255.255، یا 91.98.0.0 تا 91.99.255.255). به فرمت استاندارد IPv4 (مثلاً 5.200.123.45).\n";
    $prompt .= "**فرمت JSON:**\n";
    $prompt .= "هر کامنت به طور مثال باید به این شکل باشه:\n";
    $prompt .= "{\n";
    $prompt .= "    \"name\": \"نام رندوم\",\n";
    $prompt .= "    \"question\": \"سوال\",\n";
    $prompt .= "    \"answer\": \"پاسخ\",\n";
    $prompt .= "    \"date\": \"YYYY/MM/DD\",\n";
    $prompt .= "    \"time\": \"HH:MM\",\n";
    $prompt .= "    \"comment_email\": \"ایمیل رندوم\",\n";
    $prompt .= "    \"reply_author\": \"$reply_author\",\n";
    $prompt .= "    \"reply_email\": \"$reply_email\",\n";
    $prompt .= "    \"ip_address\": \"آی‌پی رندوم\"\n";
    $prompt .= "}\n\n";
    $prompt .= "باتوجه به موارد بالا به تعدادی که گفتم در زمان بندی ای که خواستم برام کامنت های سوال و جواب و دیتای های دیگشون رو توی یه آرایه استاندارد JSON برام بفرست فقط حواست باشه نمیخواد فایل دانلودی بدی توی محیط کد برام بنویسشون که کپی کنم. همه رو توی یک پاسخ به صورت کامل بنویس و توش چیزی غیر از دیتایی که میخوام اضافه نکن.";

    wp_send_json_success($prompt);
}

// Hook to publish the comment
add_action('acs_publish_comment', 'acs_publish_comment_callback');
function acs_publish_comment_callback($transient_key) {
    global $wpdb;
    $transient_table = $wpdb->prefix . 'acs_transients';

    error_log('Starting acs_publish_comment_callback for transient: ' . $transient_key);

    // Check if transient exists
    $comment_data = acs_get_transient($transient_key);
    if (!$comment_data) {
        error_log('Transient not found or expired during publish comment: ' . $transient_key);
        // Clean up history record
        $table_name = $wpdb->prefix . 'acs_comment_history';
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        return;
    }

    // Check if already published
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $is_published = $wpdb->get_var($wpdb->prepare(
        "SELECT is_published FROM $table_name WHERE transient_key = %s",
        $transient_key
    ));
    if ($is_published == 1) {
        error_log('Comment already published for transient: ' . $transient_key);
        return;
    }

    $post_id = $comment_data['post_id'];
    $comment_author = $comment_data['comment_author'];
    $comment_email = $comment_data['comment_email'];
    $comment_content = $comment_data['comment_content'];

    $timezone = new DateTimeZone('Asia/Tehran');
    $now = new DateTime('now', $timezone);

    $comment_data_array = [
        'comment_post_ID' => $post_id,
        'comment_author' => $comment_author,
        'comment_author_email' => $comment_email,
        'comment_content' => $comment_content,
        'comment_type' => 'comment',
        'comment_parent' => 0,
        'comment_date' => $now->format('Y-m-d H:i:s'),
        'comment_date_gmt' => gmdate('Y-m-d H:i:s'),
        'comment_approved' => 1,
    ];

    error_log('Attempting to publish comment with data: ' . print_r($comment_data_array, true));
    $comment_id = wp_insert_comment($comment_data_array);
    if ($comment_id) {
        error_log('Comment published with ID: ' . $comment_id . ' for transient: ' . $transient_key);

        $updated = $wpdb->update(
            $table_name,
            ['comment_id' => $comment_id, 'is_published' => 1],
            ['transient_key' => $transient_key],
            ['%d', '%d'],
            ['%s']
        );

        if ($updated === false) {
            error_log('Failed to update history record after publishing comment: ' . $wpdb->last_error);
        } else {
            error_log('History record updated successfully for comment ID: ' . $comment_id);
        }
    } else {
        error_log('Failed to publish comment for transient: ' . $transient_key . '. Last error: ' . $wpdb->last_error);
    }
}

// Hook to publish the reply
add_action('acs_publish_reply', 'acs_publish_reply_callback');
function acs_publish_reply_callback($transient_key) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $transient_table = $wpdb->prefix . 'acs_transients';

    error_log('Attempting to publish reply for transient: ' . $transient_key);

    $comment_data = acs_get_transient($transient_key);
    if (!$comment_data) {
        error_log('Transient not found or expired during publish reply: ' . $transient_key);
        // Clean up history record
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        return;
    }

    $comment = $wpdb->get_row($wpdb->prepare("SELECT comment_id, is_published FROM $table_name WHERE transient_key = %s", $transient_key));

    if (!$comment || !$comment->comment_id || !$comment->is_published) {
        // Check if comment was published recently
        $recent_comment = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT comment_id FROM $table_name WHERE transient_key = %s AND is_published = 1",
                $transient_key
            )
        );
        if ($recent_comment && $recent_comment->comment_id) {
            $comment_id = $recent_comment->comment_id;
        } else {
            error_log('Comment ID not found or not published for transient key: ' . $transient_key);
            // Clean up
            $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
            $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
            return;
        }
    } else {
        $comment_id = $comment->comment_id;
    }

    $post_id = $comment_data['post_id'];
    $reply_author = $comment_data['reply_author'];
    $reply_email = $comment_data['reply_email'];
    $reply_content = $comment_data['reply_content'];

    $timezone = new DateTimeZone('Asia/Tehran');
    $now = new DateTime('now', $timezone);

    $reply_data = [
        'comment_post_ID' => $post_id,
        'comment_author' => $reply_author,
        'comment_author_email' => $reply_email,
        'comment_content' => $reply_content,
        'comment_type' => 'comment',
        'comment_parent' => $comment_id,
        'comment_date' => $now->format('Y-m-d H:i:s'),
        'comment_date_gmt' => gmdate('Y-m-d H:i:s'),
        'comment_approved' => 1,
    ];

    $reply_id = wp_insert_comment($reply_data);
    if ($reply_id) {
        error_log('Reply published with ID: ' . $reply_id . ' for transient: ' . $transient_key);

        // Delete from custom transients table
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
        
        // Update history record to mark reply as published
        $updated = $wpdb->update(
            $table_name,
            ['is_reply_published' => 1],
            ['transient_key' => $transient_key],
            ['%d'],
            ['%s']
        );

        if ($updated === false) {
            error_log('Failed to update history record after publishing reply: ' . $wpdb->last_error);
        } else {
            error_log('History record updated successfully for reply ID: ' . $reply_id);
        }
    } else {
        error_log('Failed to publish reply for transient: ' . $transient_key . '. Last error: ' . $wpdb->last_error);
        // Clean up history record to avoid orphaned data
        $wpdb->delete($table_name, ['transient_key' => $transient_key], ['%s']);
        $wpdb->delete($transient_table, ['transient_key' => $transient_key], ['%s']);
    }
}

// Function to handle plugin updates and database migrations
add_action('plugins_loaded', 'acs_check_db_version');
function acs_check_db_version() {
    $current_db_version = get_option('acs_db_version', '1.0');
    $plugin_version = '2.9';

    if (version_compare($current_db_version, $plugin_version, '<')) {
        acs_update_db($current_db_version, $plugin_version);
        update_option('acs_db_version', $plugin_version);
    }
}

// Database update function for future migrations
// Database update function for future migrations
function acs_update_db($current_version, $target_version) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';
    $transient_table = $wpdb->prefix . 'acs_transients';

    // Example migration: Add new columns or modify existing ones if needed
    if (version_compare($current_version, '2.9', '<')) {
        // Add ip_address column if it doesn't exist
        $column_exists = $wpdb->get_results("SHOW COLUMNS FROM $table_name LIKE 'ip_address'");
        if (empty($column_exists)) {
            $wpdb->query("ALTER TABLE $table_name ADD COLUMN ip_address VARCHAR(45) DEFAULT NULL AFTER transient_key");
            error_log('Added ip_address column to ' . $table_name);
        }

        // Ensure the transients table exists
        acs_create_transient_table();

        // Add is_reply_published column if it doesn't exist
        $reply_published_column_exists = $wpdb->get_results("SHOW COLUMNS FROM $table_name LIKE 'is_reply_published'");
        if (empty($reply_published_column_exists)) {
            $wpdb->query("ALTER TABLE $table_name ADD COLUMN is_reply_published TINYINT(1) DEFAULT 0 AFTER is_published");
            error_log('Added is_reply_published column to ' . $table_name);
        }
    }
}

// Helper function to validate IP address
function acs_validate_ip($ip) {
    if (empty($ip)) {
        return true; // IP is optional
    }
    return filter_var($ip, FILTER_VALIDATE_IP) !== false;
}

// Helper function to generate random Iranian IP address
function acs_generate_random_ip() {
    $ip_ranges = [
        ['5.200.0.0', '5.202.255.255'],
        ['185.88.0.0', '185.88.255.255'],
        ['91.98.0.0', '91.99.255.255']
    ];
    
    $range = $ip_ranges[array_rand($ip_ranges)];
    $start = ip2long($range[0]);
    $end = ip2long($range[1]);
    $random_ip = long2ip(mt_rand($start, $end));
    
    return $random_ip;
}

// Add a debug log viewer in the admin settings page (optional)
add_action('admin_menu', 'acs_add_debug_page');
function acs_add_debug_page() {
    add_submenu_page(
        'tools.php',
        'لاگ‌های دیباگ افزونه',
        'لاگ‌های دیباگ',
        'manage_options',
        'acs-debug-logs',
        'acs_debug_logs_page_callback'
    );
}

function acs_debug_logs_page_callback() {
    ?>
    <div class="wrap">
        <h1>لاگ‌های دیباگ افزونه زمان‌بندی کامنت</h1>
        <p>در این بخش می‌توانید لاگ‌های دیباگ افزونه را مشاهده کنید. این لاگ‌ها به شناسایی مشکلات کمک می‌کنند.</p>
        <?php
        $debug_log_file = WP_CONTENT_DIR . '/debug.log';
        if (file_exists($debug_log_file)) {
            $logs = file_get_contents($debug_log_file);
            $logs = explode("\n", $logs);
            $logs = array_filter($logs, function($line) {
                return strpos($line, '[Auto Comment Scheduler]') !== false || strpos($line, 'acs_') !== false;
            });
            if (!empty($logs)) {
                echo '<pre style="background: #f0f0f0; padding: 10px; max-height: 500px; overflow-y: scroll;">';
                echo esc_html(implode("\n", $logs));
                echo '</pre>';
            } else {
                echo '<p>لاگ مرتبط با افزونه یافت نشد.</p>';
            }
        } else {
            echo '<p>فایل debug.log یافت نشد. لطفاً مطمئن شوید که دیباگ در وردپرس فعال است (WP_DEBUG_LOG = true).</p>';
        }
        ?>
    </div>
    <?php
}

// Ensure proper timezone handling for all scheduled events
add_filter('cron_schedules', 'acs_add_custom_cron_intervals');
function acs_add_custom_cron_intervals($schedules) {
    $schedules['acs_five_minutes'] = [
        'interval' => 300, // 5 minutes in seconds
        'display' => 'هر ۵ دقیقه (برای زمان‌بندی کامنت)'
    ];
    return $schedules;
}

// Schedule a recurring task to check for missed schedules (safety net)
if (!wp_next_scheduled('acs_check_missed_schedules')) {
    wp_schedule_event(time(), 'acs_five_minutes', 'acs_check_missed_schedules');
}
add_action('acs_check_missed_schedules', 'acs_check_missed_schedules_callback');
function acs_check_missed_schedules_callback() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';

    $timezone = new DateTimeZone('Asia/Tehran');
    $now = new DateTime('now', $timezone);
    $current_time = $now->format('Y-m-d H:i:s');

    // Find comments that should have been published but haven't been
    $missed_comments = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT * FROM $table_name WHERE scheduled_time <= %s AND is_published = 0",
            $current_time
        )
    );

    foreach ($missed_comments as $comment) {
        $transient_key = $comment->transient_key;
        // Check if the scheduled events still exist
        $comment_event = wp_get_scheduled_event('acs_publish_comment', [$transient_key]);
        $reply_event = wp_get_scheduled_event('acs_publish_reply', [$transient_key]);

        if (!$comment_event) {
            // Reschedule or publish immediately
            error_log('Missed comment schedule detected for transient: ' . $transient_key . '. Publishing now.');
            acs_publish_comment_callback($transient_key);
        }
        if (!$reply_event) {
            // Check if comment was published, then publish reply
            $updated_comment = $wpdb->get_row(
                $wpdb->prepare("SELECT is_published FROM $table_name WHERE transient_key = %s", $transient_key)
            );
            if ($updated_comment && $updated_comment->is_published) {
                error_log('Missed reply schedule detected for transient: ' . $transient_key . '. Publishing now.');
                acs_publish_reply_callback($transient_key);
            }
        }
    }
}

// Add a shortcode to display scheduled comments on the frontend (optional)
add_shortcode('acs_scheduled_comments', 'acs_display_scheduled_comments');
function acs_display_scheduled_comments($atts) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'acs_comment_history';

    $atts = shortcode_atts(['post_id' => get_the_ID()], $atts);
    $post_id = intval($atts['post_id']);

    $future_comments = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT * FROM $table_name WHERE post_id = %d AND scheduled_time > %s AND is_published = 0 ORDER BY scheduled_time ASC",
            $post_id,
            current_time('mysql')
        )
    );

    if (empty($future_comments)) {
        return '<p>هیچ کامنت زمان‌بندی‌شده‌ای برای نمایش وجود ندارد.</p>';
    }

    $output = '<div class="acs-scheduled-comments">';
    $output .= '<h3>کامنت‌های زمان‌بندی‌شده</h3>';
    $output .= '<ul>';
    foreach ($future_comments as $comment) {
        $datetime = new DateTime($comment->scheduled_time, new DateTimeZone('UTC'));
        $datetime->setTimezone(new DateTimeZone('Asia/Tehran'));
        list($g_y, $g_m, $g_d) = explode('-', $datetime->format('Y-m-d'));
        list($hour, $minute) = explode(':', $datetime->format('H:i'));
        list($j_y, $j_m, $j_d) = gregorian_to_jalali($g_y, $g_m, $g_d);
        $jalali_date = sprintf('%d/%02d/%02d %02d:%02d', $j_y, $j_m, $j_d, $hour, $minute);

        $output .= '<li>';
        $output .= '<strong>' . esc_html($comment->comment_author) . '</strong> - ';
        $output .= 'زمان انتشار: ' . esc_html($jalali_date);
        $output .= '<p>کامنت: ' . esc_html($comment->comment_content) . '</p>';
        $output .= '<p>پاسخ: ' . esc_html($comment->reply_content) . ' (توسط ' . esc_html($comment->reply_author) . ')</p>';
        $output .= '</li>';
    }
    $output .= '</ul>';
    $output .= '</div>';

    return $output;
}

// Add basic CSS for the shortcode display
add_action('wp_enqueue_scripts', 'acs_enqueue_frontend_styles');
function acs_enqueue_frontend_styles() {
    wp_enqueue_style('acs-frontend', plugin_dir_url(__FILE__) . 'assets/acs-frontend.css', [], '2.9');
}

?>