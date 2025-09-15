# create_wordpress_plugin.py - WordPress Plugin کامل
from pathlib import Path

print("🔌 ایجاد WordPress Plugin...")
print("=" * 40)

def create_plugin_main_file():
    """ایجاد فایل اصلی WordPress Plugin"""
    content = '''<?php
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
?>'''
    
    # ایجاد پوشه WordPress plugin
    plugin_dir = Path("wordpress_plugin") / "chaboktool-connector"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = plugin_dir / "chaboktool-connector.php"
    file_path.write_text(content, encoding='utf-8')
    print("✅ WordPress Plugin اصلی ایجاد شد")

def create_plugin_templates():
    """ایجاد template های WordPress Plugin"""
    
    # ایجاد پوشه templates
    templates_dir = Path("wordpress_plugin") / "chaboktool-connector" / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # settings-page.php
    settings_content = '''<div class="wrap">
    <h1>تنظیمات ChabokTool</h1>
    
    <form method="post" action="">
        <table class="form-table">
            <tr>
                <th scope="row">کلید مجوز</th>
                <td>
                    <input type="text" name="license_key" value="<?php echo esc_attr($this->license_key); ?>" class="regular-text" />
                    <p class="description">کلید مجوز خود را از پلتفرم ChabokTool دریافت کنید.</p>
                </td>
            </tr>
        </table>
        
        <?php submit_button('ذخیره تنظیمات'); ?>
    </form>
    
    <?php if ($this->license_key): ?>
    <div class="postbox">
        <h3 class="hndle">ماژول‌های فعال</h3>
        <div class="inside">
            <?php if (!empty($this->user_modules)): ?>
                <?php foreach ($this->user_modules as $user_module): ?>
                    <div class="chaboktool-module-card">
                        <h4><?php echo esc_html($user_module['module']['name']); ?></h4>
                        <p>نوع: <?php echo esc_html($user_module['module']['type']); ?></p>
                        <p>نسخه: <?php echo esc_html($user_module['module']['version']); ?></p>
                        <span class="status active">فعال</span>
                    </div>
                <?php endforeach; ?>
            <?php else: ?>
                <p>هیچ ماژول فعالی یافت نشد.</p>
            <?php endif; ?>
        </div>
    </div>
    <?php endif; ?>
</div>'''
    
    (templates_dir / "settings-page.php").write_text(settings_content, encoding='utf-8')
    
    # comment-scheduler-metabox.php
    metabox_content = '''<div id="chaboktool-comment-scheduler">
    <div class="chaboktool-form-group">
        <label>نویسنده کامنت:</label>
        <input type="text" id="comment_author" placeholder="نام نویسنده" />
    </div>
    
    <div class="chaboktool-form-group">
        <label>ایمیل:</label>
        <input type="email" id="comment_email" placeholder="ایمیل نویسنده" />
    </div>
    
    <div class="chaboktool-form-group">
        <label>متن کامنت:</label>
        <textarea id="comment_content" rows="4" placeholder="متن کامنت..."></textarea>
    </div>
    
    <div class="chaboktool-form-group">
        <label>زمان انتشار:</label>
        <input type="datetime-local" id="schedule_time" />
    </div>
    
    <div class="chaboktool-form-group">
        <button type="button" id="schedule_comment_btn" class="button button-primary">
            زمان‌بندی کامنت
        </button>
    </div>
    
    <div id="scheduled_comments_list">
        <!-- لیست کامنت‌های زمان‌بندی شده -->
    </div>
</div>'''
    
    (templates_dir / "comment-scheduler-metabox.php").write_text(metabox_content, encoding='utf-8')
    print("✅ Template های WordPress Plugin ایجاد شدند")

def create_plugin_assets():
    """ایجاد CSS و JS برای WordPress Plugin"""
    
    # ایجاد پوشه assets
    assets_dir = Path("wordpress_plugin") / "chaboktool-connector" / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # admin.css
    css_content = '''.chaboktool-module-card {
    border: 1px solid #ddd;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
    background: #fff;
}

.chaboktool-form-group {
    margin: 10px 0;
}

.chaboktool-form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.chaboktool-form-group input,
.chaboktool-form-group textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 3px;
}

.status.active {
    background: #46b450;
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 12px;
}

#chaboktool-comment-scheduler {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 5px;
}

.scheduled-comment {
    background: #fff;
    border: 1px solid #ddd;
    padding: 10px;
    margin: 5px 0;
    border-radius: 3px;
}'''
    
    (assets_dir / "admin.css").write_text(css_content, encoding='utf-8')
    
    # admin.js
    js_content = '''jQuery(document).ready(function($) {
    
    $('#schedule_comment_btn').click(function() {
        var postId = $('#post_ID').val();
        var author = $('#comment_author').val();
        var email = $('#comment_email').val();
        var content = $('#comment_content').val();
        var scheduleTime = $('#schedule_time').val();
        
        if (!author || !content || !scheduleTime) {
            alert('لطفاً تمام فیلدها را پر کنید');
            return;
        }
        
        $.ajax({
            url: chaboktool_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'chaboktool_schedule_comment',
                nonce: chaboktool_ajax.nonce,
                post_id: postId,
                author: author,
                email: email,
                content: content,
                schedule_time: scheduleTime
            },
            success: function(response) {
                if (response.success) {
                    alert('کامنت با موفقیت زمان‌بندی شد');
                    loadScheduledComments();
                    // پاک کردن فرم
                    $('#comment_author, #comment_email, #comment_content, #schedule_time').val('');
                } else {
                    alert('خطا: ' + response.data.message);
                }
            },
            error: function() {
                alert('خطا در ارتباط با سرور');
            }
        });
    });
    
    function loadScheduledComments() {
        var postId = $('#post_ID').val();
        
        $.ajax({
            url: chaboktool_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'chaboktool_get_scheduled_comments',
                nonce: chaboktool_ajax.nonce,
                post_id: postId
            },
            success: function(response) {
                if (response.success && response.data.comments) {
                    var html = '<h4>کامنت‌های زمان‌بندی شده:</h4>';
                    response.data.comments.forEach(function(comment) {
                        html += '<div class="scheduled-comment">';
                        html += '<strong>' + comment.comment_author + '</strong> - ';
                        html += '<em>' + comment.scheduled_time + '</em><br>';
                        html += comment.comment_content.substring(0, 100) + '...';
                        html += '</div>';
                    });
                    $('#scheduled_comments_list').html(html);
                }
            }
        });
    }
    
    // بارگذاری کامنت‌ها در ابتدا
    if ($('#post_ID').length) {
        loadScheduledComments();
    }
});'''
    
    (assets_dir / "admin.js").write_text(js_content, encoding='utf-8')
    print("✅ CSS و JS WordPress Plugin ایجاد شدند")

def main():
    """اجرای اصلی"""
    create_plugin_main_file()
    create_plugin_templates()
    create_plugin_assets()
    
    print("\n🎉 WordPress Plugin کامل ایجاد شد!")
    print("📁 مسیر: wordpress_plugin/chaboktool-connector/")
    print("\n🔄 مراحل بعدی:")
    print("1. فولدر chaboktool-connector رو zip کن")
    print("2. در وردپرس آپلود و فعال کن")
    print("3. از پنل ادمین Django یه UserModule برای تست بساز")
    print("4. license key رو در WordPress وارد کن")
    
    input("\nبرای خروج Enter بزنید...")

if __name__ == "__main__":
    main()