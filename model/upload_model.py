from huggingface_hub import login, upload_folder


login()


upload_folder(folder_path="./modelo_final_xlmr_v2", repo_id="alexoladom/prompt_guard_xlmr", repo_type="model")