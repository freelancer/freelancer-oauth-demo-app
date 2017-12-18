$(document).ready(function() {
        function getProfileImage() {
            var image_url = null;
            $.ajax({
                type: "GET",
                async: false,
                url: '/api/v1/user/profile_image',
                success: function(data) {
                    result_url = data.result.url;
                    result_key = data.result.key;
                    result_original_url = data.result.original_url;
                    if (result_url != null || result_original_url != null) {
                        image_url = result_url;
                        image_key = result_key;
                        image_original_url = result_original_url;
                    } else {
                        image_url = "build/css/img/nophoto.png";
                        image_key = "";
                        image_original_url = "build/css/img/nophoto.png";
                    }
                }
              });
            return {url: image_url, key: image_key, original_url: image_original_url};
        }

        var modal = document.getElementById('uploadModal');
        var btn = document.getElementById("Update-profile-pic");

        // Get the <span> element that closes the modal
        var span = document.getElementsByClassName("close")[0];

        // When the user clicks the button, open the modal
        btn.onclick = function() {
            $('#modal-error').html('');
            var preview = document.getElementById('profileImagePreview');
            //$("#fileupload").replaceWith($("#fileupload").val('').clone(true));
            preview.onload = function() {
                var pos = $('#drag-box').position()
                var y = pos.top;
                var x = pos.left;

                resizeBoxes(
                    y, $('#profileImagePreview').height() - y - $('#drag-box').height(),
                    $('#profileImagePreview').width() - x - $('#drag-box').width(), x,
                    $('#profileImagePreview').height()
                );
            }
            image_data = getProfileImage();
            preview.src = image_data['original_url'];
            document.getElementById('file-key').value = image_data['key'];
            modal.style.display = "block";
        }

        // When the user clicks on <span> (x), close the modal
        span.onclick = function() {
            modal.style.display = "none";
        }

        // When the user clicks anywhere outside of the modal, close it
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }

        function updatePreview() {
            var imageData = getProfileImage();
            if (imageData['url'] != null) {
                document.getElementById('Thumb-img').src = getProfileImage()['url'];
            } else if (imageData['original_url'] != null) {
                document.getElementById('Thumb-img').src = getProfileImage()['original_url'];
            }
        }

        updatePreview();

        $(function () {
            $('#fileupload').fileupload({
                dataType: 'json',
                done: function (e, data) {
                    if (data.xhr().status == 200) {
                        $('#modal-error').html('');
                        document.getElementById('file-key').value = data.result.result.key;
                        var preview = document.getElementById('profileImagePreview');
                        //$("#fileupload").replaceWith($("#fileupload").val('').clone(true));
                        preview.onload = function() {
                            var bot =  $('#profileImagePreview').height() - y - $('#drag-box').height();
                            if (bot < 0) {
                                $('#drag-box').height($('#profileImagePreview').height() - pos.top);
                                $('#drag-box').width($('#drag-box').height());
                            }

                            resizeBoxes(
                                y, $('#profileImagePreview').height() - y - $('#drag-box').height(),
                                $('#profileImagePreview').width() - x - $('#drag-box').width(), x,
                                $('#profileImagePreview').height()
                            );
                        }
                        document.getElementById('profileImagePreview').src = data.result.result.raw_url;
                        var pos = $('#drag-box').position()
                        var y = pos.top;
                        var x = pos.left;

                        updatePreview();
                    }
                },
                replaceFileInput: false,
                error: function(data) {
                    $("#fileupload").replaceWith($("#fileupload").val('').clone(true));
                    var parsed = JSON.parse(data.responseText);
                    $('#modal-error').html(parsed['message']);
                }
            });
        });

        $( "#image-submit" ).submit(function( event ) {
 
          // Stop form from submitting normally
          event.preventDefault();
         
          // Get some values from elements on the page:
          var $form = $( this ),
            imagekey = document.getElementById('file-key').value,
            url = '/api/v1/user/profile_image',
            cropx = $('#drag-box').attr('data-x'),
            cropy = $('#drag-box').attr('data-y'),
            cropwidth =  $('#drag-box').width(),
            cropheight =  $('#drag-box').height(),
            viewwidth = $('#profileImagePreview').width(),
            viewheight = $('#profileImagePreview').height();

          if (cropx == null) {
            cropx = 0
          };

          if (cropy == null) {
            cropy = 0
          };

          if (imagekey == null || imagekey == "") {
            $('#modal-error').html("Please select a file to upload");
            return;
          }
         
          // Send the data using post
          var posting = $.ajax({
            type: "POST",
            url: url,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            data: JSON.stringify({
                key: imagekey,
                crop_x: parseInt(cropx),
                crop_y: parseInt(cropy),
                crop_width: cropwidth,
                crop_height: cropheight,
                view_width: viewwidth,
                view_height: viewheight
            }),
            success: function(data) {
                document.getElementById('Thumb-img').src = data.result.url + "?" + new Date().getTime();
                modal.style.display = "none";
            },
            error: function(data) {
                var parsed = JSON.parse(data.responseText);
                $('#modal-error').html(parsed['message']);
            }
          })
        });

        function resizeBoxes(top, bot, right, left, totalheight) {
            $('#top-box').css('height', top + 'px');
            $('#bot-box').css('height', bot + 'px');
            $('#right-box').css('width', right + 'px');
            $('#right-box').css('top', top + 'px');
            var boxheight = totalheight - bot - top;
            $('#right-box').css('height', boxheight + 'px');
            $('#left-box').css('width', left + 'px');
            $('#left-box').css('top', top + 'px');
            $('#left-box').css('height', boxheight + 'px');
        }

        function dragMoveListener (event) {
            var target = event.target,
                // keep the dragged position in the data-x/data-y attributes
                x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx,
                y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

            var x_valid = (x >= 0 && x + $(event.target).width() <= $('#profileImagePreview').width());
            var y_valid = (y >= 0 && y + $(event.target).height() <= $('#profileImagePreview').height());
            // translate the element
            
            if (x_valid && y_valid) {
                target.style.webkitTransform =
                target.style.transform =
                  'translate(' + x + 'px, ' + y + 'px)';

                resizeBoxes(
                    y, $('#profileImagePreview').height() - y - $('#drag-box').height(),
                    $('#profileImagePreview').width() - x - $('#drag-box').width(), x,
                    $('#profileImagePreview').height()
                );
            }

            // update the posiion attributes
            if (x_valid) {
                target.setAttribute('data-x', x);
            }
            if (y_valid) {
                target.setAttribute('data-y', y);
            }
          }

          // this is used later in the resizing and gesture demos
          window.dragMoveListener = dragMoveListener;

        interact('#drag-box')
          .draggable({
            onmove: window.dragMoveListener
          })
          .resizable({
            preserveAspectRatio: true,
            edges: { left: true, right: true, bottom: true, top: true }
          })
          .on('resizemove', function (event) {
            var target = event.target,
                x = (parseFloat(target.getAttribute('data-x')) || 0),
                y = (parseFloat(target.getAttribute('data-y')) || 0);

            newwidth = event.rect.width;
            newheight = event.rect.height;

            x += event.deltaRect.left;
            y += event.deltaRect.top;

            
            var x_valid = (x >= 0 && x + newwidth <= $('#profileImagePreview').width());
            var y_valid = (y >= 0 && y + newheight <= $('#profileImagePreview').height());
            
            if (x_valid && y_valid && newwidth > 10 && newheight > 10) {
            
                // update the element's style
                target.style.width  = event.rect.width + 'px';
                target.style.height = event.rect.height + 'px';

                target.style.webkitTransform = target.style.transform =
                    'translate(' + x + 'px,' + y + 'px)';

                // translate the element
                
                target.setAttribute('data-x', x);
                target.setAttribute('data-y', y);
                resizeBoxes(
                    y, $('#profileImagePreview').height() - y - newheight,
                    $('#profileImagePreview').width() - x - newwidth, x,
                    $('#profileImagePreview').height()
                );
            }
          });
    
          
    });
