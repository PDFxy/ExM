	<div class="container">
	<div class="incoming container"></div>
		<div class="jumbotron">
			<h1>BOSP<small>Beidou OpenSource Project</small></h1>
			<br>
			<div class="well">
				<h2 class="text-center">At your service</h2>
				<br>
 		%if not data['user']:
				<p class="text-center"><a class="btn btn-info btn-large btn-block" href="/signup">Sign up</a></p>
		%else:
				<p class="text-center"><a class="btn btn-info btn-large btn-block" href="/ExM/">Access BOSP mail service</a></p>
		%end
		  	</div>
		</div>
	</div>
<script type="text/javascript">
	$('.navhome').addClass('active');
</script>

%rebase warper.tpl data=data