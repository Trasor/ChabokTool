<?php
/**
 * Plugin Name: ChabokTool Connector
 * Plugin URI: https://chaboktool.com
 * Description: اتصال به پلتفرم ChabokTool برای استفاده از ماژول‌های SEO
 * Version: 1.0.0
 * Author: ChabokTool Team
 * Text Domain: chaboktool-connector
 * Domain Path: /languages
 */

// جلوگیری از دسترسی مستقیم
if (!defined('ABSPATH')) {
    exit;
}

// تعریف constants
define('CHABOKTOOL_VERSION', '1.0.0');
define('CHABOKTOOL_PLUGIN_URL', plugin_dir_url(__FILE__));
define('CHABOKTOOL_PLUGIN_PATH', plugin_dir_path(__FILE__));

class ChabokToolConnector {
    
    private $api_url = 'http://127.0.0.1:8000/api/';
    private $license_key = '';
    private $user_modules = array();
    
    public function __construct() {
        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'admin_scripts'));
        
        // AJAX handlers
        add_action('wp_ajax_chaboktool_verify_license', array($this, 'ajax_verify_license'));
        add_action('wp_ajax_chaboktool_schedule_comment', array($this, 'ajax_schedule_comment'));
        add_action('wp_ajax_chaboktool_get_scheduled_comments', array($this, 'ajax_get_scheduled_comments'));
        
        // Hooks
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
    }
    
    public function init() {
        // بارگذاری زبان
        load_plugin_textdomain('chaboktool-connector', false, dirname(plugin_basename(__FILE__)) . '/languages');
        
        // دریافت license key
        $this->license_key = get_option('chaboktool_license_key', '');
        
        // بارگذاری ماژول‌های فعال
        if ($this->license_key) {
            $this->load_user_modules();
            $this->init_active_modules();
        }
    }
    
    public function admin_menu() {
        add_menu_page(
            'ChabokTool',
            'ChabokTool', 
            'manage_options',
            'chaboktool',
            array($this, 'admin_page'),
            'data:image/svg+xml;base64,' . base64_encode('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'),
            30
        );
        
        add_submenu_page(
            'chaboktool',
            'تنظیمات',
            'تنظیمات',
            'manage_options',
            'chaboktool-settings',
            array($this, 'settings_page')
        );
    }
    
    public function admin_scripts($hook) {
        if (strpos($hook, 'chaboktool') !== false || get_post_type() == 'post') {
            wp_enqueue_style('chaboktool-admin', CHABOKTOOL_PLUGIN_URL . 'assets/admin.css', array(), CHABOKTOOL_VERSION);
            wp_enqueue_script('chaboktool-admin', CHABOKTOOL_PLUGIN_URL . 'assets/admin.js', array('jquery'), CHABOKTOOL_VERSION);
            
            wp_localize_script('chaboktool-admin', 'chaboktool_ajax', array(
                'ajax_url' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('chaboktool_nonce'),
                'api_url' => $this->api_url,
                'license_key' => $this->license_key,
                'user_modules' => $this->user_modules
            ));
        }
    }
    
    public function admin_page() {
        include(CHABOKTOOL_PLUGIN_PATH . 'templates/admin-page.php');
    }
    
    public function settings_page() {
        if (isset($_POST['submit'])) {
            $license_key = sanitize_text_field($_POST['license_key']);
            
            if ($this->verify_license($license_key)) {
                update_option('chaboktool_license_key', $license_key);
                $this->license_key = $license_key;
                echo '<div class="notice notice-success"><p>مجوز با موفقیت فعال شد!</p></div>';
            } else {
                echo '<div class="notice notice-error"><p>مجوز معتبر نیست!</p></div>';
            }
        }
        
        include(CHABOKTOOL_PLUGIN_PATH . 'templates/settings-page.php');
    }
    
    private function verify_license($license_key) {
        $domain = parse_url(home_url(), PHP_URL_HOST);
        
        $response = wp_remote_post($this->api_url . 'accounts/login/', array(
            'body' => json_encode(array(
                'license_key' => $license_key,
                'domain' => $domain
            )),
            'headers' => array(
                'Content-Type' => 'application/json'
            ),
            'timeout' => 30
        ));
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        return $status_code === 200;
    }
    
    private function load_user_modules() {
        $response = wp_remote_get($this->api_url . 'modules/user-modules/', array(
            'headers' => array(
                'Authorization' => 'Bearer ' . $this->license_key
            ),
            'timeout' => 30
        ));
        
        if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
            $body = wp_remote_retrieve_body($response);
            $data = json_decode($body, true);
            
            if (isset($data['user_modules'])) {
                $this->user_modules = $data['user_modules'];
            }
        }
    }
    
    private function init_active_modules() {
        foreach ($this->user_modules as $user_module) {
            $module = $user_module['module'];
            
            switch ($module['id']) {
                case '14dedda7-654f-4723-bb4f-2e5734ca6973': // Comment Scheduler ID
                    $this->init_comment_scheduler();
                    break;
            }
        }
    }
    
    private function init_comment_scheduler() {
        // اضافه کردن metabox برای posts
        add_action('add_meta_boxes', function() {
            add_meta_box(
                'chaboktool-comment-scheduler',
                'زمان‌بندی کامنت - ChabokTool',
                array($this, 'comment_scheduler_metabox'),
                ['post', 'page']
            );
        });
    }
    
    public function comment_scheduler_metabox($post) {
        wp_nonce_field('chaboktool_comment_scheduler', 'chaboktool_nonce');
        include(CHABOKTOOL_PLUGIN_PATH . 'templates/comment-scheduler-metabox.php');
    }
    
    public function ajax_verify_license() {
        check_ajax_referer('chaboktool_nonce', 'nonce');
        
        $license_key = sanitize_text_field($_POST['license_key']);
        
        if ($this->verify_license($license_key)) {
            wp_send_json_success(array('message' => 'مجوز معتبر است'));
        } else {
            wp_send_json_error(array('message' => 'مجوز معتبر نیست'));
        }
    }
    
    public function ajax_schedule_comment() {
        check_ajax_referer('chaboktool_nonce', 'nonce');
        
        $post_id = intval($_POST['post_id']);
        $author = sanitize_text_field($_POST['author']);
        $email = sanitize_email($_POST['email']);
        $content = sanitize_textarea_field($_POST['content']);
        $schedule_time = sanitize_text_field($_POST['schedule_time']);
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'chaboktool_scheduled_comments';
        
        $result = $wpdb->insert(
            $table_name,
            array(
                'post_id' => $post_id,
                'comment_content' => $content,
                'comment_author' => $author,
                'comment_author_email' => $email,
                'scheduled_time' => $schedule_time,
                'status' => 'scheduled',
                'created_at' => current_time('mysql')
            ),
            array('%d', '%s', '%s', '%s', '%s', '%s', '%s')
        );
        
        if ($result !== false) {
            wp_send_json_success(array(
                'message' => 'کامنت با موفقیت زمان‌بندی شد',
                'id' => $wpdb->insert_id
            ));
        } else {
            wp_send_json_error(array('message' => 'خطا در ذخیره‌سازی'));
        }
    }
    
    public function ajax_get_scheduled_comments() {
        check_ajax_referer('chaboktool_nonce', 'nonce');
        
        $post_id = intval($_POST['post_id']);
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'chaboktool_scheduled_comments';
        
        $results = $wpdb->get_results($wpdb->prepare(
            "SELECT * FROM $table_name WHERE post_id = %d AND status = 'scheduled' ORDER BY scheduled_time ASC",
            $post_id
        ));
        
        wp_send_json_success(array('comments' => $results));
    }
    
    public function activate() {
        $this->create_tables();
    }
    
    public function deactivate() {
        // پاک‌سازی اختیاری
    }
    
    private function create_tables() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'chaboktool_scheduled_comments';
        
        $charset_collate = $wpdb->get_charset_collate();
        
        $sql = "CREATE TABLE $table_name (
            id int(11) NOT NULL AUTO_INCREMENT,
            post_id int(11) NOT NULL,
            comment_content text NOT NULL,
            comment_author varchar(255) NOT NULL,
            comment_author_email varchar(255),
            comment_author_url varchar(255),
            scheduled_time datetime NOT NULL,
            status varchar(20) DEFAULT 'scheduled',
            comment_id int(11),
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY post_id (post_id),
            KEY scheduled_time (scheduled_time),
            KEY status (status)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }
}

// شروع plugin
new ChabokToolConnector();
?>