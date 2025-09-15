<div id="chaboktool-comment-scheduler">
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
</div>