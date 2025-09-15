jQuery(document).ready(function($) {
    // Toggle history details
    $('.acs-history-toggle').on('click', function() {
        $(this).parent().next('.acs-history-details').slideToggle();
        $(this).text($(this).text() === ' (نمایش جزئیات)' ? ' (بستن جزئیات)' : ' (نمایش جزئیات)');
    });

    // Accordion functionality
    $('.acs-accordion-title').on('click', function() {
        $(this).next('.acs-accordion-content').slideToggle();
        $('.acs-accordion-content').not($(this).next()).slideUp();
    });

    // Initialize Persian Datepicker
    $('.acs-date-picker').persianDatepicker({
        format: 'YYYY/MM/DD',
        autoClose: true,
        initialValue: false,
        toolbox: {
            calendarSwitch: {
                enabled: true
            }
        }
    });

    // Show/hide bulk delete button based on checkbox selection
    $('.acs-history-checkbox').on('change', function() {
        if ($('.acs-history-checkbox:checked').length > 0) {
            $('#acs-bulk-delete-btn').show();
        } else {
            $('#acs-bulk-delete-btn').hide();
        }
    });

    // Schedule comment manually
    $('#acs-schedule-btn').on('click', function() {
        var postId = $('#post_ID').val();
        var commentAuthor = $('#acs-comment-author').val();
        var commentEmail = $('#acs-comment-email').val();
        var commentContent = $('#acs-comment-content').val();
        var replyAuthor = $('#acs-reply-author').val();
        var replyEmail = $('#acs-reply-email').val();
        var replyContent = $('#acs-reply-content').val();
        var date = $('#acs-date').val();
        var time = $('#acs-time').val();
        var minutes = $('#acs-minutes').val();

        $('#acs-error').hide();
        $('#acs-success').hide();

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_save_comment',
                nonce: acs_vars.nonce,
                post_id: postId,
                comment_author: commentAuthor,
                comment_email: commentEmail,
                comment_content: commentContent,
                reply_author: replyAuthor,
                reply_email: replyEmail,
                reply_content: replyContent,
                date: date,
                time: time,
                minutes: minutes
            },
            success: function(response) {
                if (response.success) {
                    $('#acs-success').text(response.data).show();
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    $('#acs-error').text(response.data.message).show();
                    if (response.data.empty_fields) {
                        $.each(response.data.empty_fields, function(field, isEmpty) {
                            if (isEmpty) {
                                $('#acs-' + field).addClass('error');
                            } else {
                                $('#acs-' + field).removeClass('error');
                            }
                        });
                    }
                }
            },
            error: function() {
                $('#acs-error').text('خطا در ارتباط با سرور').show();
            }
        });
    });

    // Schedule comments from JSON
    $('#acs-json-schedule-btn').on('click', function() {
        var postId = $('#post_ID').val();
        var jsonText = $('#acs-json-text').val();

        $('#acs-json-error').hide();
        $('#acs-json-success').hide();

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_process_json',
                nonce: acs_vars.nonce,
                post_id: postId,
                json_text: jsonText
            },
            success: function(response) {
                if (response.success) {
                    $('#acs-json-success').text(response.data).show();
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    $('#acs-json-error').text(response.data).show();
                }
            },
            error: function() {
                $('#acs-json-error').text('خطا در ارتباط با سرور').show();
            }
        });
    });

    // Generate prompt for AI
    $('#acs-generate-prompt-btn').on('click', function(e) {
        e.preventDefault();

        // Debug: Check if elements exist in DOM
        const elementsToCheck = [
            'acs-prompt-reply-author',
            'acs-prompt-reply-email',
            'acs-date-time',
            'acs-tone-details',
            'acs-extra-conditions',
            'post_ID'
        ];
        let missingElements = [];
        elementsToCheck.forEach(id => {
            if ($(`#${id}`).length === 0) {
                missingElements.push(id);
            }
        });
        if (missingElements.length > 0) {
            console.error('Missing elements in DOM:', missingElements);
            alert('خطا: برخی از المنت‌های مورد نیاز در صفحه یافت نشدند. لطفاً با توسعه‌دهنده تماس بگیرید.');
            return;
        }

        const replyAuthor = $('#acs-prompt-reply-author').val() || '';
        const replyEmail = $('#acs-prompt-reply-email').val() || '';
        const dateTime = $('#acs-date-time').val() || '';
        const toneDetails = $('#acs-tone-details').val() || '';
        const extraConditions = $('#acs-extra-conditions').val() || '';

        // Check if at least one field is filled
        const anyFieldFilled = replyAuthor || replyEmail || dateTime || toneDetails || extraConditions;

        // If no field is filled, show a message (user can still update the post)
        if (!anyFieldFilled) {
            alert('لطفاً حداقل یکی از فیلدها را پر کنید تا پرامپت تولید شود.');
            return;
        }

        // If at least one field is filled, all required fields must be filled
        if (!replyAuthor || !replyEmail || !dateTime || !toneDetails) {
            alert('لطفاً تمام فیلدهای الزامی را پر کنید');
            return;
        }

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_generate_prompt',
                nonce: acs_vars.generate_prompt_nonce,
                post_ID: $('#post_ID').val(),
                reply_author: replyAuthor,
                reply_email: replyEmail,
                date_time: dateTime,
                tone_details: toneDetails,
                extra_conditions: extraConditions
            },
            success: function(response) {
                if (response.success) {
                    $('#acs-prompt-result').html('<textarea class="widefat" rows="10" readonly>' + response.data + '</textarea>').show();
                    $('#acs-copy-prompt-container').show();
                    $('#acs-copy-prompt-message').hide();
                } else {
                    alert('خطا: ' + response.data);
                }
            },
            error: function() {
                alert('خطا در ارتباط با سرور');
            }
        });
    });

    // Copy prompt to clipboard
    $('#acs-copy-prompt-btn').on('click', function() {
        var promptText = $('#acs-prompt-result textarea').val();
        navigator.clipboard.writeText(promptText).then(function() {
            $('#acs-copy-prompt-message').show();
            setTimeout(function() {
                $('#acs-copy-prompt-message').fadeOut();
            }, 2000);
        }).catch(function(err) {
            alert('خطا در کپی کردن پرامپت: ' + err);
        });
    });

    // Edit comment
    $('.acs-edit-btn').on('click', function() {
        var $item = $(this).closest('.acs-history-item');
        var commentId = $item.data('id');
        var transientKey = $item.data('transient-key');

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_get_comment',
                nonce: acs_vars.get_comment_nonce,
                comment_id: commentId
            },
            success: function(response) {
                if (response.success) {
                    var data = response.data;
                    $('#edit-comment-id').val(commentId);
                    $('#edit-comment-author').val(data.comment_author);
                    $('#edit-comment-email').val(data.comment_email);
                    $('#edit-comment-content').val(data.comment_content);
                    $('#edit-reply-author').val(data.reply_author);
                    $('#edit-reply-email').val(data.reply_email);
                    $('#edit-reply-content').val(data.reply_content);
                    $('#edit-date').val(data.date);
                    $('#edit-time').val(data.time);
                    $('#edit-ip-address').val(data.ip_address);
                    $('#acs-edit-form').show();

                    // Reinitialize Persian Datepicker for edit form
                    $('#edit-date').persianDatepicker({
                        format: 'YYYY/MM/DD',
                        autoClose: true,
                        initialValue: true,
                        toolbox: {
                            calendarSwitch: {
                                enabled: true
                            }
                        }
                    });

                    // Scroll to edit form
                    $('html, body').animate({
                        scrollTop: $('#acs-edit-form').offset().top
                    }, 500);
                } else {
                    alert('خطا: ' + response.data);
                }
            },
            error: function() {
                alert('خطا در ارتباط با سرور');
            }
        });
    });

    // Save edited comment
    $('#acs-save-edit-btn').on('click', function() {
        var commentId = $('#edit-comment-id').val();
        var commentAuthor = $('#edit-comment-author').val();
        var commentEmail = $('#edit-comment-email').val();
        var commentContent = $('#edit-comment-content').val();
        var replyAuthor = $('#edit-reply-author').val();
        var replyEmail = $('#edit-reply-email').val();
        var replyContent = $('#edit-reply-content').val();
        var date = $('#edit-date').val();
        var time = $('#edit-time').val();
        var ipAddress = $('#edit-ip-address').val();
        var transientKey = $('.acs-history-item[data-id="' + commentId + '"]').data('transient-key');
        var postId = $('#post_ID').val();

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_update_comment',
                nonce: acs_vars.update_comment_nonce,
                comment_id: commentId,
                transient_key: transientKey,
                post_id: postId,
                comment_author: commentAuthor,
                comment_email: commentEmail,
                comment_content: commentContent,
                reply_author: replyAuthor,
                reply_email: replyEmail,
                reply_content: replyContent,
                date: date,
                time: time,
                ip_address: ipAddress
            },
            success: function(response) {
                if (response.success) {
                    alert(response.data);
                    location.reload();
                } else {
                    alert('خطا: ' + response.data);
                }
            },
            error: function() {
                alert('خطا در ارتباط با سرور');
            }
        });
    });

    // Cancel edit
    $('#acs-cancel-edit-btn').on('click', function() {
        $('#acs-edit-form').hide();
    });

    // Delete comment
    $('.acs-delete-btn').on('click', function() {
        if (!confirm('آیا مطمئن هستید که می‌خواهید این کامنت را حذف کنید؟')) {
            return;
        }

        var $item = $(this).closest('.acs-history-item');
        var commentId = $item.data('id');
        var transientKey = $item.data('transient-key');

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_delete_comment',
                nonce: acs_vars.nonce,
                comment_ids: [commentId],
                transient_keys: [transientKey]
            },
            success: function(response) {
                if (response.success) {
                    $item.remove();
                    alert(response.data);
                } else {
                    alert('خطا: ' + response.data);
                }
            },
            error: function() {
                alert('خطا در ارتباط با سرور');
            }
        });
    });

    // Bulk delete comments
    $('#acs-bulk-delete-btn').on('click', function() {
        var commentIds = [];
        var transientKeys = [];

        $('.acs-history-checkbox:checked').each(function() {
            var $item = $(this).closest('.acs-history-item');
            commentIds.push($item.data('id'));
            transientKeys.push($item.data('transient-key'));
        });

        if (commentIds.length === 0) {
            alert('لطفاً حداقل یک کامنت را انتخاب کنید');
            return;
        }

        if (!confirm('آیا مطمئن هستید که می‌خواهید کامنت‌های انتخاب‌شده را حذف کنید؟')) {
            return;
        }

        $.ajax({
            url: acs_vars.ajax_url,
            type: 'POST',
            data: {
                action: 'acs_delete_comment',
                nonce: acs_vars.nonce,
                comment_ids: commentIds,
                transient_keys: transientKeys
            },
            success: function(response) {
                if (response.success) {
                    $('.acs-history-checkbox:checked').closest('.acs-history-item').remove();
                    $('#acs-bulk-delete-btn').hide();
                    alert(response.data);
                } else {
                    alert('خطا: ' + response.data);
                }
            },
            error: function() {
                alert('خطا در ارتباط با سرور');
            }
        });
    });
});