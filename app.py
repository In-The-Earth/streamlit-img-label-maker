import streamlit as st
import os
from PIL import Image
from streamlit_img_label import st_img_label
from streamlit_img_label.manage import ImageManager, ImageDirManager

def get_save_directory():
    """ให้ผู้ใช้ระบุโฟลเดอร์สำหรับบันทึกไฟล์"""
    save_dir = st.sidebar.text_input("Save Directory", value="img_dir", help="Enter the directory to save files.")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir

def upload_class_file():
    """ฟังก์ชันสำหรับอัปโหลดและอ่าน labels จาก class.txt"""
    uploaded_file = st.sidebar.file_uploader(
        "Upload class.txt", type=["txt"], help="Upload a text file with one label per line."
    )
    if uploaded_file is not None:
        labels = [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines()]
        st.session_state["labels"] = labels
        st.success("Labels updated successfully!")
    else:
        labels = st.session_state.get("labels", ["", "dog", "cat"])  # Default labels
    return labels

def run():
    # อัปโหลด class.txt และกำหนด Labels
    labels = upload_class_file()

    # สร้าง ImageDirManager
    save_dir = get_save_directory()
    idm = ImageDirManager(save_dir)

    if "files" not in st.session_state:
        st.session_state["files"] = idm.get_all_files()
        st.session_state["annotation_files"] = idm.get_exist_annotation_files()
        st.session_state["image_index"] = 0
    else:
        idm.set_all_files(st.session_state["files"])
        idm.set_annotation_files(st.session_state["annotation_files"])

    def refresh():
        st.session_state["files"] = idm.get_all_files()
        st.session_state["annotation_files"] = idm.get_exist_annotation_files()
        st.session_state["image_index"] = 0

    def next_image():
        image_index = st.session_state["image_index"]
        if image_index < len(st.session_state["files"]) - 1:
            st.session_state["image_index"] += 1
        else:
            st.warning('This is the last image.')

    def previous_image():
        image_index = st.session_state["image_index"]
        if image_index > 0:
            st.session_state["image_index"] -= 1
        else:
            st.warning('This is the first image.')

    def next_annotate_file():
        image_index = st.session_state["image_index"]
        next_image_index = idm.get_next_annotation_image(image_index)
        if next_image_index:
            st.session_state["image_index"] = idm.get_next_annotation_image(image_index)
        else:
            st.warning("All images are annotated.")
            next_image()

    def go_to_image():
        file_index = st.session_state["files"].index(st.session_state["file"])
        st.session_state["image_index"] = file_index

    # Sidebar: Upload Images
    with st.sidebar.expander("Upload Images"):
        uploaded_files = st.file_uploader(
            "Choose images to upload", accept_multiple_files=True, type=["jpg", "png", "jpeg"]
        )
        if uploaded_files:
            if st.button("Upload"):
                for uploaded_file in uploaded_files:
                    with open(os.path.join(save_dir, uploaded_file.name), "wb") as f:
                        f.write(uploaded_file.getbuffer())
                st.success(f"Uploaded {len(uploaded_files)} images to {save_dir}")
                refresh()

    # Sidebar: show status
    n_files = len(st.session_state["files"])
    n_annotate_files = len(st.session_state["annotation_files"])
    st.sidebar.write("Total files:", n_files)
    st.sidebar.write("Total annotate files:", n_annotate_files)
    st.sidebar.write("Remaining files:", n_files - n_annotate_files)

    st.sidebar.selectbox(
        "Files",
        st.session_state["files"],
        index=st.session_state["image_index"],
        on_change=go_to_image,
        key="file",
    )
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.button(label="Previous image", on_click=previous_image)
    with col2:
        st.button(label="Next image", on_click=next_image)
    st.sidebar.button(label="Next need annotate", on_click=next_annotate_file)
    st.sidebar.button(label="Refresh", on_click=refresh)

    # Main content: annotate images
    img_file_name = idm.get_image(st.session_state["image_index"])
    img_path = os.path.join(save_dir, img_file_name)
    im = ImageManager(img_path)
    img = im.get_img()
    resized_img = im.resizing_img()
    resized_rects = im.get_resized_rects()
    rects = st_img_label(resized_img, box_color="red", rects=resized_rects)

    def annotate():
        im.save_annotation()
        image_annotate_file_name = img_file_name.split(".")[0] + ".xml"
        if image_annotate_file_name not in st.session_state["annotation_files"]:
            st.session_state["annotation_files"].append(image_annotate_file_name)
        next_annotate_file()

    if rects:
        st.button(label="Save", on_click=annotate)
        preview_imgs = im.init_annotation(rects)

        for i, prev_img in enumerate(preview_imgs):
            prev_img[0].thumbnail((200, 200))
            col1, col2 = st.columns(2)
            with col1:
                col1.image(prev_img[0])
            with col2:
                default_index = 0
                if prev_img[1]:
                    default_index = labels.index(prev_img[1])

                select_label = col2.selectbox(
                    "Label", labels, key=f"label_{i}", index=default_index
                )
                im.set_annotation(i, select_label)

if __name__ == "__main__":
    run()
