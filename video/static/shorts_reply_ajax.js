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
    while (replies.length > 2) {
      const oldest = replies.shift();
      oldest?.remove();
    }
    updateReplyCount(comment, data.reply_count);
  };

  const submitReply = async (form) => {
    const button = form.querySelector('button[type="submit"]');
    const textarea = form.querySelector('textarea[name="comment"]');
    const error = ensureError(form);
    error.hidden = true;
    if (button) button.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json',
        },
      });
      if (!response.ok) throw new Error('reply request failed');
      const data = await response.json();
      renderReply(form, data);
      if (textarea) textarea.value = '';
      const details = form.closest('details');
      if (details) details.open = false;
    } catch (_) {
      error.hidden = false;
    } finally {
      if (button) button.disabled = false;
    }
  };

  feed.addEventListener('submit', (event) => {
    const form = event.target.closest('.shorts-reply-form');
    if (!form) return;
    event.preventDefault();
    submitReply(form);
  });
})();
