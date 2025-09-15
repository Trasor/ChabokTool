jQuery(document).ready(function($) {
    
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
});