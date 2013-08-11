<!DOCTYPE html>
<html lang="zh_CN">
  <head>
	<meta charset="utf-8">
	<title>Beidou OpenSource Project</title>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="description" content="Beidou OpenSource Project">
	<meta name="author" content="avastms@jhxs.org">

	<!-- Le styles -->
	<link href="/static/css/bootstrap.min.css" rel="stylesheet">
	<link href="/static/css/bootstrap-glyphicons.css" rel="stylesheet">
	
	<!--link href="/static/css/jquery-ui-1.9.2.custom.css" rel="stylesheet"-->
	<style type="text/css">
	  body { padding-top: 70px; }
	  .cHidden{ display:none; }
	  .cPaddTop{padding-top: 13%;}
	</style>

	<!-- HTML5 shim, for IE6-8 support of HTML5 elements -->
	<!--[if lt IE 9]>
	  <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
	<![endif]-->
	<script type="text/javascript" src="/static/js/jquery-2.0.3.min.js"></script>
	<script type="text/javascript" src="/static/js/jquery.sha1.js"></script>
	<script type="text/javascript" src="/static/js/jquery.form.js"></script>
	<script type="text/javascript" src="/static/js/bootstrap.min.js"></script>
	<script type="text/javascript" src="/static/js/jquery.scrollTo.min.js"></script>


  </head>

  <body data-spy="scroll" data-target=".navbar">

 	<div class="navbar navbar-fixed-top navbar-inverse">
 	<div class="container">
 		<a href="/" class="navbar-brand">BOSP</a>
 		<ul class="nav navbar-nav">
 			<li class="navhome">
 				<a href="/">Home</a>
 			</li>
 			<li class="navExM">
 				<a href="/ExM/">Mail Service</a>
 			</li>
 		</ul>
 		%if not data['user']:
		<span class="pull-right preSign">
			<a href="/signup" class="btn navbar-btn btn-default navsignup">Sign up</a>
			&nbsp;
			<a href="#signinModal" data-target="#signinModal" data-toggle="modal" class="btn navbar-btn btn-success navsignin">Sign in</a>
		</span>
		%else:
		<span class="pull-right postSign">
			<a href="/signout" class="btn navbar-btn btn-warning navsignout">Sign out</a>
		</span>
		%end
	</div>
	</div>
  <div class="signin-modal modal fade" id="signinModal">
    <div class="modal-dialog cPaddTop">
      <div class="modal-content">
		<form class="form-horizontal ajaxform" action="/signin" method="POST">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
          <h3 class="modal-title">I AM THE COMMUNITY &nbsp;<small>Sign in to BOSP</small></h3>
        </div>
        <div class="modal-body">
        	<div class="col-lg-offset-2">
				<div class="form-group">
				  <label for="email" class="col-lg-2 control-label">Email</label>
				  <div class="col-lg-6">
				    <input type="email" class="form-control" name="_id" id="email" placeholder="Email" required="1">
				  </div>
				</div>
				<div class="form-group">
				  <label for="inputPassword" class="col-lg-2 control-label">Password</label>
				  <div class="col-lg-6">
				    <input type="password" class="passwd-d form-control" name="passwd" id="inputPassword" placeholder="Password" required="1">
				    <input type="hidden" class="salt" name="salt" value="">
				  </div>
				</div>
			</div>
        </div>
        <div class="modal-footer">
          <a href="#" data-dismiss='modal' class="btn btn-default">Cancle</a>
          <button type="submit" class="btn btn-success freeze">Sign in</button>
        </div>
		</form>
      </div><!-- /.modal-content -->
    </div><!-- /.modal-dialog -->
  </div><!-- /.modal -->

	%include

	<div class="container">
	<hr>
	  <footer>
		<p>&copy; Brought to you by <a href=""></a> avastms@ibeidou.net  <img class="pull-right" src="http://www.python.org/community/logos/python-powered-w-140x56.png"></p>
	  </footer>

	</div> <!-- /container -->

	<!-- Le javascript
	================================================== -->
	<!-- Placed at the end of the document so the pages load faster -->


	<script type="text/javascript">
			staticSalt= function(str){
				return $.sha1('bosp'+str)
			};
			dynamicSalt= function(str,salt) {
				return $.sha1(str+salt)
			};
			$('.salt').val(Math.random());


        $(document).ready(function(){
          $('.ajaxform').ajaxForm({
				target: '.incoming',
				error: function(e){
				  $('.incoming').html(e.responseText);
				  $.scrollTo('.incoming',300,{offset:{top:-50}})
				  $(".freeze").removeAttr('disabled');
				  $(".modal").modal('hide');
				},
				beforeSerialize: function(){
				  $('.passwd-d').val(dynamicSalt(staticSalt($('.passwd-d').val()), $('.salt').val()) );
				  $('.passwd-s').val(staticSalt($('.passwd-s').val()));
				},
				beforeSubmit: function(){
				  $(".freeze").attr('disabled','1');
				},
				success: function(){
				  $.scrollTo('.incoming',300,{offset:{top:-50}})
				  $(".freeze").removeAttr('disabled');
				  $(".modal").modal('hide');
				},
				clearForm: false,
          	});
          });

	</script>

  </body>
</html>