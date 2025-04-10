                # Don't delete the file yet as we might need it for the fallback approach
                return False, f"Subprocess error: {str(se)}"
            # Clean up temporary file if we created one and command was successful
            if result.returncode == 0 and using_temp_file and os.path.exists(safe_path):
                os.unlink(safe_path)
                logger.info(f"Removed temporary file: {safe_path}")
            # If the command failed, we'll keep the file for the fallback attempt
                # Ensure the file exists before trying fallback
                if not os.path.exists(safe_path):
                    logger.error(f"File not found for fallback upload: {safe_path}")
                    return False, f"Fallback upload error: File not found"

                # Use a new file path for the fallback attempt to avoid any issues
                fallback_path = os.path.join(os.path.dirname(safe_path), f"fallback_{uuid.uuid4().hex[:8]}{file_ext}")
                try:
                    # Make a fresh copy for the fallback attempt
                    shutil.copy2(safe_path, fallback_path)
                    logger.info(f"Created copy for fallback attempt: {fallback_path}")
                    
                    simple_cmd = [self.rmapi_path, "put", fallback_path, self.upload_folder]
                    logger.info(f"Running fallback command: {' '.join(simple_cmd)}")
                    
                    fallback_result = subprocess.run(
                        simple_cmd,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    # Log detailed command output for debugging
                    logger.info(f"Fallback command exit code: {fallback_result.returncode}")
                    if fallback_result.stdout:
                        logger.info(f"Fallback command stdout: {fallback_result.stdout}")
                    if fallback_result.stderr:
                        logger.warning(f"Fallback command stderr: {fallback_result.stderr}")
                    
                    # Clean up both temporary files
                    if os.path.exists(fallback_path):
                        os.unlink(fallback_path)
                        logger.info(f"Removed fallback temporary file: {fallback_path}")
                    if using_temp_file and os.path.exists(safe_path):
                        os.unlink(safe_path)
                        logger.info(f"Removed original temporary file: {safe_path}")
                    
                    if fallback_result.returncode == 0:
                        logger.info("Fallback upload succeeded")
                        return True, f"Document uploaded to Remarkable using fallback method: {title}"
                    else:
                        logger.error(f"Fallback upload also failed: {fallback_result.stderr}")
                except Exception as fallback_error:
                    logger.error(f"Error in fallback upload: {fallback_error}")
                    # Clean up any remaining temporary files
                    if os.path.exists(fallback_path):
                        os.unlink(fallback_path)
                    if using_temp_file and os.path.exists(safe_path):
                        os.unlink(safe_path)
                
                return False, f"Upload error: {error_msg}"
            logger.error(f"Exception in n-flag upload method: {e}")
