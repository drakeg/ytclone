(() => {
  const feed = document.getElementById('shorts-feed');
  if (!feed) return;

  const ensureError = (form) => {
    let error = form.querySelector('[data-short-reply-error]');
    if (!error) {
      error = document.createElement('span');
      error.className = 'small text-danger ms-2';
      error.dataset.shortReplyError = '';
      error.setAttribute('role', 'status');
      error.hidden = true;
      error.textContent = 'Could not post reply.';
      form.appendChild(error);
    }
    return error;
  };

  const updateReplyCount = (comment, count) => {
    let label = comment.querySelector('[data-short-reply-count]');
    if (!label) {
      label = comment.querySelector('.video-meta.mt-1');
      if (!label) {
        label = document.createElement('div');
        label.className = 'video-meta mt-1';
        const details = comment.querySelector('details');
        comment.insertBefore(label, details || null);
      }
      label.dataset.shortReplyCount = '';
    }
    label.textContent = `${count} ${count === 1 ? 'reply' : 'replies'}`;
  };

  const renderReply = (form, data) => {
    const comment = form.closest('.shorts-comment');
    if (!comment) return;
    const reply = document.createElement('div');
    reply.className = 'shorts-reply';
    reply.dataset.shortReplyId = String(data.id);
    const author = document.createElement('strong');
    author.textContent = `@${data.author}`;
    const when = document.createElement('span');
    when.className = 'video-meta';
    when.textContent = ' just now';
    const body = document.createElement('div');
    body.textContent = data.comment;
    reply.append(author, when, body);
    const details = form.closest('details');
    comment.insertBefore(reply, details || null);
    const replies = [...comment.querySelectorAll(':scope > .shorts-reply')];
    while (replies.length > 2) replies.shift()?.remove();
    updateReplyCount(comment, data.reply_count);
  };

  const submitReply = async (form) => {
    const button = form.querySelector('button[type="submit"]');
    const textarea = form.querySelector('textarea[name="comment"]');
    const error = ensureError(form);
    error.hidden = true;
    if (button) button.disabled = true;
    try {
      const response = await fetch(form.action, {method:'POST', body:new FormData(form), headers:{'X-Requested-With':'XMLHttpRequest','Accept':'application/json'}});
      if (!response.ok) throw new Error('reply request failed');
      const data = await response.json();
      renderReply(form, data);
      if (textarea) textarea.value = '';
      const details = form.closest('details');
      if (details) details.open = false;
    } catch (_) { error.hidden = false; }
    finally { if (button) button.disabled = false; }
  };

  const renderComment = (form, data) => {
    const section = form.closest('.shorts-comments');
    const empty = section?.querySelector('[data-short-no-comments]');
    const count = section?.querySelector('[data-short-comment-count]');
    if (!section) return;
    empty?.remove();
    if (count) count.textContent = data.comment_count;
    const comment = document.createElement('div');
    comment.className = 'shorts-comment';
    comment.dataset.shortCommentId = String(data.id);
    const author = document.createElement('strong'); author.textContent = `@${data.author}`;
    const when = document.createElement('span'); when.className = 'video-meta'; when.textContent = ' just now';
    const body = document.createElement('div'); body.textContent = data.comment;
    comment.append(author, when, body);
    const details = document.createElement('details'); details.className = 'mt-2';
    const summary = document.createElement('summary'); summary.className = 'small'; summary.textContent = 'Reply';
    const replyForm = document.createElement('form'); replyForm.className = 'shorts-reply-form mt-2'; replyForm.method = 'post'; replyForm.action = data.reply_url;
    const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]')?.cloneNode(true);
    const textarea = document.createElement('textarea'); textarea.className = 'form-control form-control-sm mb-2'; textarea.name = 'comment'; textarea.required = true; textarea.placeholder = `Reply to @${data.author}…`; textarea.setAttribute('aria-label', `Reply to ${data.author}`);
    const button = document.createElement('button'); button.className = 'btn btn-sm btn-outline-primary'; button.type = 'submit'; button.textContent = 'Post reply';
    if (csrf) replyForm.append(csrf);
    replyForm.append(textarea, button); details.append(summary, replyForm); comment.append(details);
    form.parentNode.insertBefore(comment, form);
  };

  const submitComment = async (form) => {
    const error = form.querySelector('[data-short-comment-error]');
    const button = form.querySelector('button[type="submit"]');
    const textarea = form.querySelector('textarea[name="comment"]');
    if (error) error.style.display = 'none';
    if (button) button.disabled = true;
    try {
      const response = await fetch(form.action, {method:'POST', body:new FormData(form), headers:{'X-Requested-With':'XMLHttpRequest','Accept':'application/json'}});
      const data = await response.json();
      if (!response.ok) throw new Error(data?.errors ? 'validation' : 'comment request failed');
      renderComment(form, data); form.reset(); textarea?.focus();
    } catch (_) { if (error) error.style.display = 'inline'; }
    finally { if (button) button.disabled = false; }
  };

  feed.addEventListener('submit', (event) => {
    const replyForm = event.target.closest('.shorts-reply-form');
    if (replyForm) { event.preventDefault(); submitReply(replyForm); return; }
    const commentForm = event.target.closest('[data-short-comment-form]');
    if (commentForm) { event.preventDefault(); submitComment(commentForm); }
  });
})();
