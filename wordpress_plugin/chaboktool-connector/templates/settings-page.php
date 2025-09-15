<div class="wrap">
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
</div>