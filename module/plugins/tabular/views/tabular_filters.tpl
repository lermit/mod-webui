%import json

%filters = filters2
<script>
  filter_properties = {{json.dumps(filter_properties)}};
  filters = {{json.dumps(filters)}};
  hst_properties = {{json.dumps(hst_properties)}};
  hp_properties = {{json.dumps(hp_properties)}};
  sst_properties = {{json.dumps(sst_properties)}};
  sp_properties = {{json.dumps(sp_properties)}};
</script>

<div>
  <form name='filtering' id='filtering' class='span12'>
    <div id='filtering_cont'>
      
    </div>
  </form>
</div>




<!-- Div about the host status types -->
<div id='filtering_hst_panel' class='filter_value_panel well hide'>
  <a href="javascript:submit_hst_panel();"><i class="icon-ok"></i></a>
  <a title="remove all" href="javascript:remove_all_hst_panel();"><i class="icon-remove-circle"></i></a>
  <table id='filtering_hst_table'>
  </table>
</div>


<!-- Div about the host properties -->
<div id='filtering_hp_panel' class='filter_value_panel well hide'>
  <a href="javascript:submit_hp_panel();"><i class="icon-ok"></i></a>
  <a title="remove all" href="javascript:remove_all_hp_panel();"><i class="icon-remove-circle"></i></a>
  <table id='filtering_hp_table'>
  </table>
</div>

<!-- Div about the services status types -->
<div id='filtering_sst_panel' class='filter_value_panel well hide'>
  <a href="javascript:submit_sst_panel();"><i class="icon-ok"></i></a>
  <a title="remove all" href="javascript:remove_all_sst_panel();"><i class="icon-remove-circle"></i></a>
  <table id='filtering_sst_table'>
  </table>
</div>


<!-- Div about the services properties -->
<div id='filtering_sp_panel' class='filter_value_panel well hide'>
  <a href="javascript:submit_sp_panel();"><i class="icon-ok"></i></a>
  <a title="remove all" href="javascript:remove_all_sp_panel();"><i class="icon-remove-circle"></i></a>
  <table id='filtering_sp_table'>
  </table>
</div>
