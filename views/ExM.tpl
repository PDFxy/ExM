<div class="container">
	<div class="page-header">
		<h1>E-mail Facility &nbsp;<small>Set you email redirections.</small></h1>
	</div>
	<div class="incoming container"></div>
	<div class="row">
		<div class="col-8 col-lg-6 col-lg-offset-3">
			<form class="form-horizontal ajaxform" action="./set" method="POST">
				<div class="form-group">
				  <label for="email" class="col-lg-3 control-label">Origin address</label>
				  <div class="col-lg-8">
				    <input type="email" class="form-control" name="from" id="origin" placeholder="eg. you@bosp.ibeidou.net" required="1" value="{{data['ExM']['_id'] if data['ExM'] else ''}}">
				    <p class="help-block">The Email address you would like to have on bosp.ibeidou.net</p>

				  </div>
				</div>
				<div class="form-group">
				  <label for="inputPassword" class="col-lg-3 control-label">Target address</label>
				  <div class="col-lg-8">
				    <input type="email" class="form-control" name="to" id="target" placeholder="eg. you@gmail.com" required="1" value="{{data['ExM']['to'] if data['ExM'] else data['user']['_id']}}">
				    <p class="help-block">The Alias address which you already have. All mails will be forwarded to this address.</p>
				  </div>
				</div>
				<div class="form-group">
				  <div class="col-lg-offset-9 col-lg-6">
				    <button type="submit" class="btn btn-success freeze">Set Now</button>
				  </div>
				</div>
			</form>
		</div>
	</div>


</div>
<script type="text/javascript">
	$('.navExM').addClass('active');
</script>
%rebase warper.tpl data=data