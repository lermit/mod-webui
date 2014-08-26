/*Copyright (C) 2009-2011 :
     Gabes Jean, naparuba@gmail.com
     Gerhard Lausser, Gerhard.Lausser@consol.de
     Gregory Starck, g.starck@gmail.com
     Hartmut Goebel, h.goebel@goebel-consult.de

 This file is part of Shinken.

 Shinken is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Shinken is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
*/


/* We Hide all detail elements */
$(document).ready(function(){
    // By default hide all "hide" chevron of the right part
    $('.chevron-up').hide();
});


$(document).ready(function(){
	$('.applytooltip').tooltip({html:true});
    });

/*
  Look for Shift key up and down
*/
is_shift_pressed = false;
function shift_pressed(){
    is_shift_pressed = true;
}

function shift_released(){
    is_shift_pressed = false;
}

$(document).bind('keydown', 'shift', shift_pressed);
$(document).bind('keyup', 'shift', shift_released);

/*
  If we keep the shift pushed and hovering over selections, it
  select the elements. Easier for massive selection :)
*/
function hovering_selection(name){
    if(is_shift_pressed){
	add_element(name);
    }
}


/*
  Tool bar related code
*/

function hide_toolbar(){
    $('#toolbar').hide();
    $('#hide_toolbar_btn').hide();
    $('#show_toolbar_btn').show();
    save_toolbar('hide');
}

function show_toolbar(){
    $('#toolbar').show();
    $('#hide_toolbar_btn').show();
    $('#show_toolbar_btn').hide();
    save_toolbar('show');
}

function save_toolbar(toolbar){
    console.log('Need to save toolbar pref '+toolbar);
    $.post("/user/save_pref", { 'key' : 'toolbar', 'value' : toolbar});
}



/* And if the user lick on the good image, we untoggle them. */
function show_detail(name){
    var myFx = $('#'+name).slideToggle();
    $('#show-detail-'+name).toggle();
    $('#hide-detail-'+name).toggle();
}


// The user ask to show the hidden problems that are duplicated
function show_hidden_problems(cls){
    $('.'+cls).show();
    // And hide the vvv button
    $('#btn-'+cls).hide();
}

// At start we hide the unselect all button
$(document).ready(function(){
	//$('#unselect_all_btn').hide();
    $('.btn_show_when_selection').hide();
    /*
    if(toolbar_hide){
        hide_toolbar();
    }else{
        $('#show_toolbar_btn').hide();
    }
    */

    // If actions are not allowed, disable the button 'select all'
    if(!actions_enabled){
	$('#select_all_btn').addClass('disabled');
	// And put in opacity low the 'selectors'
	$('.tick').css({'opacity' : 0.4});
    }
});


// At start we hide the selected images
// and the actions tabs
$(document).ready(function(){
    $('.img_tick').hide();
});



function toggle_select_buttons(){
    /*
      $('#select_all_btn').toggle();
      $('#unselect_all_btn').toggle();
    */
    
    $('.btn_hide_when_selection').toggle();
    $('.btn_show_when_selection').toggle();
}

function show_unselect_all_button(){
    /*
    $('#select_all_btn').hide();
    $('#unselect_all_btn').show();
    */
    $('.btn_hide_when_selection').hide();
    $('.btn_show_when_selection').show();
}

function show_select_all_button(){
    /*$('#unselect_all_btn').hide();
      $('#select_all_btn').show();*/

    $('.btn_hide_when_selection').show();
    $('.btn_show_when_selection').hide();
}

// When we select all, add all in the selected list,
// and hide the select all button, and swap it with
// unselect all one
function select_all_problems(){
    // Maybe the actions are not allwoed. If so, don't act
    if(!actions_enabled){return;}

    toggle_select_buttons();
    /*$('#select_all_btn').hide();
    $('#unselect_all_btn').show();*/

    // we wil lget all elements by looking at .details and get their ids
    $('.element').each(function(){
	add_element($(this).attr('id'));
    });
}

// guess what? unselect is the total oposite...
function unselect_all_problems(){
    toggle_select_buttons();
    /*$('#unselect_all_btn').hide();
    $('#select_all_btn').show();*/
    flush_selected_elements();
}


/* We keep an array of all selected elements */
var selected_elements = [];

function add_remove_elements(name){
    // Maybe the actions are not allwoed. If so, don't act
    if(!actions_enabled){return;}


    //alert(selected_elements.indexOf(name));
    if( selected_elements.indexOf(name) != -1 ){
	remove_element(name);
    }else{
	add_element(name);
    }
}


/* function when we add an element*/
function add_element(name){
    selected_elements.push(name);

    // We put the select all button in unselect mode
    show_unselect_all_button();

    // We show the 'tick' image ofthe selector on the left
    $('#selector-'+name).show();

    /* The user will ask something, so it's good to reinit
       the refresh time so he got time to launch its action,
       see reload.js for this function 
    */
    reinit_refresh();
}

/* And or course when we remove it... */
function remove_element(name){
    selected_elements.remove(name);
    if(selected_elements.length == 0){
	show_select_all_button();
    }
    // And hide the tick image
    $('#selector-'+name).hide();
}


/* Flush selected elements, so clean the list
but also untick thems in the UI */
function flush_selected_elements(){
    /* We must copy the list so we can parse it in a clean way
     without fearing some bugs */
    var cpy = $.extend({}, selected_elements);
    $.each(cpy, function(idx, name) {
	remove_element(name);
    });
}


/* Jquery need simple id, so no / or space. So we get in the #id
the data-raw-obj-name to get the unchanged name*/
function unid_name(name){
    return $('#'+name).attr('data-raw-obj-name');
}

/* Now actions buttons : */
function recheck_now_all(){
    $.each(selected_elements,function(idx, name){
	    console.log('RECHECK?'+idx+''+name+' '+unid_name(name));
	recheck_now(unid_name(name));
    });
    flush_selected_elements();
}


/* Now actions buttons : */
function submit_check_ok_all(){
    $.each(selected_elements, function(idx, name){
        submit_check(unid_name(name), '0', 'Forced OK from WebUI');
    });
    flush_selected_elements();
}


/* Now actions buttons : */
function try_to_fix_all(){
    $.each(selected_elements, function(idx, name){
        try_to_fix(unid_name(name));
    });
    flush_selected_elements();
}


function acknowledge_all(user){
    $.each(selected_elements, function(idx, name){
	do_acknowledge(unid_name(name), 'Acknowledged from WebUI by '+user, user);
    });
    flush_selected_elements();
}


function remove_all(user){
    $.each(selected_elements, function(idx, name){
        do_remove(unid_name(name), 'Removed from WebUI by '+user, user);
    });
    flush_selected_elements();
}










// OPTIONS
var is_table_options_div_shown = false;
$(function(){
	$('#table_options_div').hide();
    });


function display_table_options(){
    var orig_a = a;
    var a = $('#btn-options');
    var pos = a[0].getBoundingClientRect();
    console.log('GO TO'+pos.left);
    var div = $('#table_options_div');
    div.css('left', pos.left - 100 );
    div.css('top' , pos.top  + 20);
    div.show();
}

function toggle_table_options(){
    if(is_table_options_div_shown){
	close_table_options();
	is_table_options_div_shown = false;
    }else{
	display_table_options();
	is_table_options_div_shown = true;
    }
}

function close_table_options(){
    $('#table_options_div').hide();
}



function apply_form_options(){
    var checkboxes = $("#table_options_div:checkbox");
    console.log(checkboxes.length);
    var realms = [];
    for(var i=0; i<checkboxes.length; i++){
	var box = $(checkboxes[i]);
	var b = (box.attr('checked') == 'checked');
	console.log(b);
	console.log(box.attr('name'));
    }
}






var tabular_cols = [
		    {name:'state', id:1, display:'State'},
		    {name:'duration',  'id':2, display:'Duration'},
		    {name:'output', id:3, display:'Output'},
		    {name:'state-type', id:4, display:'State Type'},
		    {name:'last-check', id:5, display:'Last check'},
		    {name:'attempts', id:6, display:'Attempts'},
		    {name:'realm', id:7, display:'Realm'},
		    {name:'business-impact', id:8, display:'Priority'},
		    ];


$(function(){
	// If cols was never changed, put the default value instead
	if(cols == 0){
	    cols = 398;
	}
	var f = $('#table_options_form');
	for (var i=0; i<tabular_cols.length; i++){
	    var e = tabular_cols[i];
	    var s = '<label class="checkbox"> <input class="options-checkbox" type="checkbox" name="'+e.name+'" id="col-'+e.name+'"/>'+e.display+'</label>';
	    var o = $(s);
	    f.append(o);
	    var offset = e.id;
	    var mask = 1 << offset; // gets the ith bit
	    var m = cols & mask;
	    var b = (m != 0);
	    console.log('IS CHECKED?'+e.name+' '+b);
	    $('#col-'+e.name).attr('checked', b);
	}
	apply_cols();
	
	// When the user update the columns, compute the cols by looking at checkbox, update the
	//ta ble visibility and finally update if need the value in the user pref center.
	var checkboxes = $(".options-checkbox").on('click', function(evt){
		apply_cols();
		update_cols_cookie();
	    });
    });



function find_options_entry(name){
    for(var i=0; i<tabular_cols.length; i++){
	if(tabular_cols[i].name == name){
	    return tabular_cols[i];
	}
    }
    return null;
}

function display_options_col(n){
    $('.th-'+n).show();
    $('.td-'+n).show();
    var e = find_options_entry(n);
    var id = e.id;
    console.log('MAKE SURE THE ID'+id+' is added to col');
    //compute_col();
}

function hide_options_col(n){
    $('.th-'+n).hide();
    $('.td-'+n).hide();
    var e = find_options_entry(n);
    var id = e.id;

    console.log('MAKE SURE THE ID'+id+' is removed to col');
    //compute_col();
}

// DEFAULT VALUE FOR COL=206= state+duration+output+realm
function compute_col(){
    // Reset the cols var to 0
    cols = 0;
    var checkboxes = $(".options-checkbox");
    for(var i=0; i<checkboxes.length; i++){
	var c = $(checkboxes[i]);
	var b = (c.attr('checked') == 'checked');
	var n = c.attr('name');
	
	var e = find_options_entry(n);
	var offset = e.id;
	if(b){
	    cols |= 1 << offset;
	}
    }
    console.log('COLS?'+cols);
}

function apply_cols(){
    compute_col();
    for (var i=0; i<tabular_cols.length; i++){
	var e = tabular_cols[i];
	var offset = e.id;
	var mask = 1 << offset; // gets the ith bit
	var m = cols & mask;
	var b = (m != 0);
	if(b){
	    display_options_col(e.name);
	}else{
	    hide_options_col(e.name);
	}
    }
    
}


function update_cols_cookie(){
    $.post("/user/save_pref", { 'key' : 'tab_cols', 'value' : JSON.stringify(cols)});
}



// *********** Number of element by page

/*********** SPinner **********/
function get_small_spinner(name){
    var opts = {
        lines: 13, // The number of lines to draw
        length: 3, // The length of each line
        width: 2, // The line thickness
        radius: 2, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        color: '#000', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: '2px', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
    };
    var target = $('#'+name)[0];
    var spinner = new Spinner(opts).spin(target);
    return spinner;
}


$(function(){
	$('#table_nb_elements_sel').change(function(evt){
		console.log('Change on');
		console.log($(this).val());
		get_small_spinner('table_nb_elements_span');
		var jqxhr = $.post("/user/save_pref", { 'key' : 'tab_nb_elts', 'value' : JSON.stringify($(this).val())});
		jqxhr.done(function() {
			$('#table_nb_elements_span').empty();
			force_refresh();
		    })
	    });

	var opts = $('.table_nb_elements_opt');
	for(var i=0; i<opts.length; i++){
	    var o = $(opts[i]);
	    if( o.val() == tab_nb_elts){
		o.prop('selected', true);
	    }
	}
    });