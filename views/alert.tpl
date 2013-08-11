<div class="alert{{' alert-block' if title else ''}}{{' alert-'+type if type else ''}} {{name}} fade in">
	<button type="button" class="close lddefreeze lddismiss" data-dismiss="alert">&times;</button>
	%if title:
		<h4>{{title}}</h4>
	%end
		<p>{{!content}}</p>
</div>