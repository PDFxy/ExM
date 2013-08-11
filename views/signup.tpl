		<div class="container">
			<div class="page-header">
				<h1>Join the community &nbsp;<small>Sign up for BOSP</small></h1>
				
			</div>
			<div class="incoming container"></div>
			<div class="row">
				<div class="col-8 col-lg-6 col-lg-offset-3">
					<form class="form-horizontal ajaxform" action="/signup" method="POST">
						<div class="form-group">
						  <label for="email" class="col-lg-2 control-label">Email</label>
						  <div class="col-lg-6">
						    <input type="email" class="form-control" name="_id" id="email" placeholder="Email" required="1">
						  </div>
						</div>
						<div class="form-group">
						  <label for="inputPassword" class="col-lg-2 control-label">Password</label>
						  <div class="col-lg-6">
						    <input type="password" class="passwd-s form-control" name="passwd" id="inputPassword" placeholder="Password" required="1">
						    <input type="hidden" class="salt" name="salt" value="">
						  </div>
						</div>
						<div class="form-group">
						  <div class="col-lg-offset-6 col-lg-6">
						    <button type="submit" class="btn btn-info freeze">Sign up</button>
						  </div>
						</div>
					</form>
				</div>
			</div>
		</div>
<script type="text/javascript">
	$('.navsignup').addClass('active');
</script>
%rebase warper.tpl data=data