/* =====================================================
   COREFIX ADMIN DASHBOARD
   REPAIRS + PRODUCTS + PRODUCT IMAGE UPLOAD
===================================================== */


/* =====================================================
   REPAIR ELEMENTS
===================================================== */

const repairTableBody =
    document.getElementById("repairTableBody");

const emptyAdmin =
    document.getElementById("emptyAdmin");

const adminSearch =
    document.getElementById("adminSearch");

const clearRepairsBtn =
    document.getElementById("clearRepairsBtn");

let allRepairs = [];


/* =====================================================
   PRODUCT ELEMENTS
===================================================== */

const productForm =
    document.getElementById("productForm");

const productName =
    document.getElementById("productName");

const productPrice =
    document.getElementById("productPrice");

const productIcon =
    document.getElementById("productIcon");

const productImage =
    document.getElementById("productImage");

const productImageFile =
    document.getElementById("productImageFile");

const productImagePreview =
    document.getElementById("productImagePreview");

const productImagePreviewWrapper =
    document.getElementById(
        "productImagePreviewWrapper"
    );

const productStock =
    document.getElementById("productStock");

const productDescription =
    document.getElementById(
        "productDescription"
    );

const productTableBody =
    document.getElementById(
        "productTableBody"
    );

const emptyProducts =
    document.getElementById(
        "emptyProducts"
    );

let allProducts = [];

let editingProductId = null;


/* =====================================================
   LOAD REPAIRS
===================================================== */

async function loadRepairs() {

    if (!repairTableBody) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/admin/repairs"
            );


        const data =
            await response.json();


        if (!response.ok) {

            if (
                response.status === 401
            ) {

                window.location.href =
                    "/admin/login";

                return;
            }


            throw new Error(
                data.message ||
                "Unable to load repairs."
            );
        }


        allRepairs =
            data.repairs || [];


        displayRepairs(
            adminSearch
                ? adminSearch.value
                : ""
        );


    } catch (error) {

        console.error(
            "Admin load error:",
            error
        );


        if (emptyAdmin) {

            emptyAdmin.textContent =
                "Unable to load repair requests.";

            emptyAdmin.style.display =
                "block";
        }
    }
}


/* =====================================================
   DISPLAY REPAIRS
===================================================== */

function displayRepairs(
    searchText = ""
) {

    if (!repairTableBody) {
        return;
    }


    repairTableBody.innerHTML =
        "";


    const search =
        searchText
            .trim()
            .toLowerCase();


    const filteredRepairs =
        allRepairs.filter(
            function(repair) {

                const searchableText =
                    `
                    ${repair.repairId || ""}
                    ${repair.name || ""}
                    ${repair.phone || ""}
                    ${repair.device || ""}
                    ${repair.brand || ""}
                    ${repair.model || ""}
                    ${repair.issue || ""}
                    ${repair.status || ""}
                    `
                    .toLowerCase();


                return searchableText.includes(
                    search
                );
            }
        );


    if (
        filteredRepairs.length === 0
    ) {

        if (emptyAdmin) {

            emptyAdmin.textContent =
                "No repair requests found.";

            emptyAdmin.style.display =
                "block";
        }

    } else {

        if (emptyAdmin) {

            emptyAdmin.style.display =
                "none";
        }
    }


    filteredRepairs.forEach(
        function(repair) {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    <strong>
                        ${escapeHTML(
                            repair.repairId
                        )}
                    </strong>
                </td>


                <td>

                    ${escapeHTML(
                        repair.name
                    )}

                    <small>
                        ${escapeHTML(
                            repair.phone
                        )}
                    </small>

                </td>


                <td>

                    ${escapeHTML(
                        repair.brand
                    )}

                    ${escapeHTML(
                        repair.model
                    )}

                </td>


                <td>
                    ${escapeHTML(
                        repair.issue
                    )}
                </td>


                <td>

                    <span class="admin-status">

                        ${escapeHTML(
                            repair.status
                        )}

                    </span>

                </td>


                <td>

                    <select
                        class="status-select"
                        data-id="${escapeHTML(
                            repair.repairId
                        )}"
                    >

                        <option
                            value="Request Received"
                            ${
                                repair.status ===
                                "Request Received"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Request Received
                        </option>


                        <option
                            value="Device Inspection"
                            ${
                                repair.status ===
                                "Device Inspection"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Device Inspection
                        </option>


                        <option
                            value="Repair In Progress"
                            ${
                                repair.status ===
                                "Repair In Progress"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Repair In Progress
                        </option>


                        <option
                            value="Ready for Collection"
                            ${
                                repair.status ===
                                "Ready for Collection"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Ready for Collection
                        </option>

                    </select>

                </td>

            `;


            repairTableBody
                .appendChild(row);
        }
    );


    addStatusListeners();

    updateStats();
}


/* =====================================================
   REPAIR STATUS LISTENERS
===================================================== */

function addStatusListeners() {

    const selects =
        document.querySelectorAll(
            ".status-select"
        );


    selects.forEach(
        function(select) {

            select.addEventListener(
                "change",
                async function() {

                    const repairId =
                        this.dataset.id;

                    const newStatus =
                        this.value;


                    const repair =
                        allRepairs.find(
                            item =>
                                item.repairId ===
                                repairId
                        );


                    const oldStatus =
                        repair
                            ? repair.status
                            : "";


                    this.disabled = true;


                    try {

                        const response =
                            await fetch(
                                `/api/admin/repairs/${encodeURIComponent(
                                    repairId
                                )}/status`,
                                {
                                    method: "PUT",

                                    headers: {
                                        "Content-Type":
                                            "application/json"
                                    },

                                    body:
                                        JSON.stringify({
                                            status:
                                                newStatus
                                        })
                                }
                            );


                        const data =
                            await response.json();


                        if (!response.ok) {

                            if (
                                response.status ===
                                401
                            ) {

                                window.location.href =
                                    "/admin/login";

                                return;
                            }


                            throw new Error(
                                data.message ||
                                "Unable to update status."
                            );
                        }


                        if (repair) {

                            repair.status =
                                newStatus;
                        }


                        displayRepairs(
                            adminSearch
                                ? adminSearch.value
                                : ""
                        );


                    } catch (error) {

                        console.error(
                            "Status update error:",
                            error
                        );


                        alert(
                            error.message ||
                            "Unable to update repair status."
                        );


                        this.value =
                            oldStatus;


                    } finally {

                        this.disabled =
                            false;
                    }
                }
            );
        }
    );
}


/* =====================================================
   REPAIR STATISTICS
===================================================== */

function updateStats() {

    const totalRepairs =
        document.getElementById(
            "totalRepairs"
        );

    const receivedCount =
        document.getElementById(
            "receivedCount"
        );

    const progressCount =
        document.getElementById(
            "progressCount"
        );

    const readyCount =
        document.getElementById(
            "readyCount"
        );


    if (totalRepairs) {

        totalRepairs.textContent =
            allRepairs.length;
    }


    if (receivedCount) {

        receivedCount.textContent =
            allRepairs.filter(
                repair =>
                    repair.status ===
                    "Request Received"
            ).length;
    }


    if (progressCount) {

        progressCount.textContent =
            allRepairs.filter(
                repair =>
                    repair.status ===
                    "Repair In Progress"
            ).length;
    }


    if (readyCount) {

        readyCount.textContent =
            allRepairs.filter(
                repair =>
                    repair.status ===
                    "Ready for Collection"
            ).length;
    }
}


/* =====================================================
   REPAIR SEARCH
===================================================== */

if (adminSearch) {

    adminSearch.addEventListener(
        "input",
        function() {

            displayRepairs(
                this.value
            );
        }
    );
}


/* =====================================================
   CLEAR REPAIR DATA
===================================================== */

if (clearRepairsBtn) {

    clearRepairsBtn.addEventListener(
        "click",
        function() {

            alert(
                "Database clearing is disabled for safety."
            );
        }
    );
}


/* =====================================================
   LOAD PRODUCTS
===================================================== */

async function loadProducts() {

    if (!productTableBody) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/products"
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Unable to load products."
            );
        }


        allProducts =
            data.products || [];


        displayProducts();


    } catch (error) {

        console.error(
            "Product load error:",
            error
        );


        if (emptyProducts) {

            emptyProducts.textContent =
                "Unable to load accessories.";

            emptyProducts.style.display =
                "block";
        }
    }
}


/* =====================================================
   DISPLAY PRODUCTS
===================================================== */

function displayProducts() {

    if (!productTableBody) {
        return;
    }


    productTableBody.innerHTML =
        "";


    if (
        allProducts.length === 0
    ) {

        if (emptyProducts) {

            emptyProducts.style.display =
                "block";
        }

        return;
    }


    if (emptyProducts) {

        emptyProducts.style.display =
            "none";
    }


    allProducts.forEach(
        function(product) {

            const row =
                document.createElement(
                    "tr"
                );


            let stockClass =
                "stock-in";


            if (
                product.stockStatus ===
                "Low Stock"
            ) {

                stockClass =
                    "stock-low";
            }


            if (
                product.stockStatus ===
                "Out of Stock"
            ) {

                stockClass =
                    "stock-out";
            }


            let imagePreview = `

                <span class="no-product-image">
                    No image
                </span>

            `;


            if (
    product.image &&
    product.image.trim() !== ""
) {
    const imageUrl =
        product.image.startsWith("http://") ||
        product.image.startsWith("https://")
            ? product.image
            : `/static/assets/products/${encodeURIComponent(
                product.image
            )}`;

    imagePreview = `
        <img
            src="${escapeHTML(imageUrl)}"
            alt="${escapeHTML(
                product.name
            )}"
            class="admin-product-image"
        >
    `;
}


            row.innerHTML = `

                <td>

                    <strong>

                        ${escapeHTML(
                            product.icon || "📦"
                        )}

                        ${escapeHTML(
                            product.name
                        )}

                    </strong>


                    <small>

                        ${escapeHTML(
                            product.description
                        )}

                    </small>

                </td>


                <td>
                    ${imagePreview}
                </td>


                <td>

                    ₦${formatPrice(
                        product.price
                    )}

                </td>


                <td>

                    <span
                        class="${stockClass}"
                    >

                        ${escapeHTML(
                            product.stockStatus
                        )}

                    </span>

                </td>


                <td>

                    <button
                        type="button"
                        class="
                            product-action-btn
                            product-edit-btn
                        "
                        data-id="${product.id}"
                    >
                        Edit
                    </button>


                    <button
                        type="button"
                        class="
                            product-action-btn
                            product-delete-btn
                        "
                        data-id="${product.id}"
                    >
                        Delete
                    </button>

                </td>

            `;


            productTableBody
                .appendChild(row);
        }
    );


    addProductActionListeners();
}


/* =====================================================
   PRODUCT IMAGE PREVIEW
===================================================== */

if (productImageFile) {

    productImageFile.addEventListener(
        "change",
        function() {

            const file =
                this.files[0];


            if (!file) {

                hideProductImagePreview();

                return;
            }


            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];


            if (
                !allowedTypes.includes(
                    file.type
                )
            ) {

                alert(
                    "Please select a JPG, PNG or WEBP image."
                );


                this.value = "";


                hideProductImagePreview();

                return;
            }


            /*
               Limit image size to 5 MB
            */

            const maximumSize =
                5 * 1024 * 1024;


            if (
                file.size > maximumSize
            ) {

                alert(
                    "The image is too large. Please choose an image smaller than 5 MB."
                );


                this.value = "";


                hideProductImagePreview();

                return;
            }


            const reader =
                new FileReader();


            reader.onload =
                function(event) {

                    if (
                        productImagePreview
                    ) {

                        productImagePreview.src =
                            event.target.result;
                    }


                    if (
                        productImagePreviewWrapper
                    ) {

                        productImagePreviewWrapper
                            .style
                            .display =
                            "block";
                    }
                };


            reader.readAsDataURL(
                file
            );
        }
    );
}


/* =====================================================
   HIDE PRODUCT IMAGE PREVIEW
===================================================== */

function hideProductImagePreview() {

    if (
        productImagePreviewWrapper
    ) {

        productImagePreviewWrapper
            .style
            .display =
            "none";
    }


    if (productImagePreview) {

        productImagePreview.src =
            "";
    }
}


/* =====================================================
   UPLOAD PRODUCT IMAGE
===================================================== */

async function uploadProductImage() {

    /*
       If no new image is selected while editing,
       keep the existing filename.
    */

    if (
        !productImageFile ||
        !productImageFile.files ||
        productImageFile.files.length === 0
    ) {

        return productImage
            ? productImage.value.trim()
            : "";
    }


    const formData =
        new FormData();


    formData.append(
        "image",
        productImageFile.files[0]
    );


    const response =
        await fetch(
            "/api/admin/products/upload-image",
            {
                method: "POST",
                body: formData
            }
        );


    let data;


    try {

        data =
            await response.json();

    } catch (error) {

        throw new Error(
            "Invalid response from image upload server."
        );
    }


    if (!response.ok) {

        if (
            response.status ===
            401
        ) {

            window.location.href =
                "/admin/login";


            throw new Error(
                "Admin session expired."
            );
        }


        throw new Error(
            data.message ||
            "Unable to upload product image."
        );
    }


    return data.filename;
}


/* =====================================================
   ADD OR UPDATE PRODUCT
===================================================== */

if (productForm) {

    productForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const submitButton =
                productForm.querySelector(
                    ".product-add-btn"
                );


            if (!submitButton) {
                return;
            }


            submitButton.disabled =
                true;


            submitButton.textContent =
                editingProductId !== null
                    ? "Updating..."
                    : "Adding...";


            try {

                /* =====================================
                   BASIC VALIDATION
                ===================================== */

                const name =
                    productName
                        ? productName.value.trim()
                        : "";


                const description =
                    productDescription
                        ? productDescription.value.trim()
                        : "";


                const price =
                    productPrice
                        ? Number(
                            productPrice.value
                        )
                        : 0;


                if (!name) {

                    throw new Error(
                        "Please enter a product name."
                    );
                }


                if (!description) {

                    throw new Error(
                        "Please enter a product description."
                    );
                }


                if (
                    Number.isNaN(price) ||
                    price < 0
                ) {

                    throw new Error(
                        "Please enter a valid product price."
                    );
                }


                /* =====================================
                   UPLOAD IMAGE
                ===================================== */

                const uploadedImage =
                    await uploadProductImage();


                /* =====================================
                   CREATE PRODUCT DATA
                ===================================== */

                const productData = {

                    name:
                        name,

                    description:
                        description,

                    price:
                        price,

                    icon:
                        productIcon &&
                        productIcon.value.trim()
                            ? productIcon
                                .value
                                .trim()
                            : "📦",

                    stockStatus:
                        productStock
                            ? productStock.value
                            : "In Stock",

                    image:
                        uploadedImage
                };


                /* =====================================
                   CREATE OR UPDATE
                ===================================== */

                let url =
                    "/api/admin/products";


                let method =
                    "POST";


                const wasEditing =
                    editingProductId !==
                    null;


                if (wasEditing) {

                    url =
                        `/api/admin/products/${editingProductId}`;

                    method =
                        "PUT";
                }


                const response =
                    await fetch(
                        url,
                        {
                            method:
                                method,

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    productData
                                )
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    if (
                        response.status ===
                        401
                    ) {

                        window.location.href =
                            "/admin/login";

                        return;
                    }


                    throw new Error(
                        data.message ||
                        "Unable to save product."
                    );
                }


                alert(
                    wasEditing
                        ? "Product updated successfully."
                        : "Product added successfully."
                );


                resetProductForm();


                await loadProducts();


            } catch (error) {

                console.error(
                    "Save product error:",
                    error
                );


                alert(
                    error.message ||
                    "Unable to save product."
                );


            } finally {

                submitButton.disabled =
                    false;


                submitButton.textContent =
                    editingProductId !== null
                        ? "Update Product"
                        : "+ Add Product";
            }
        }
    );
}


/* =====================================================
   PRODUCT ACTION LISTENERS
===================================================== */

function addProductActionListeners() {

    const editButtons =
        document.querySelectorAll(
            ".product-edit-btn"
        );


    const deleteButtons =
        document.querySelectorAll(
            ".product-delete-btn"
        );


    editButtons.forEach(
        function(button) {

            button.addEventListener(
                "click",
                function() {

                    const productId =
                        Number(
                            this.dataset.id
                        );


                    startProductEdit(
                        productId
                    );
                }
            );
        }
    );


    deleteButtons.forEach(
        function(button) {

            button.addEventListener(
                "click",
                async function() {

                    const productId =
                        Number(
                            this.dataset.id
                        );


                    await deleteProduct(
                        productId
                    );
                }
            );
        }
    );
}


/* =====================================================
   START PRODUCT EDIT
===================================================== */

function startProductEdit(
    productId
) {

    const product =
        allProducts.find(
            item =>
                Number(item.id) ===
                Number(productId)
        );


    if (!product) {

        alert(
            "Product could not be found."
        );

        return;
    }


    editingProductId =
        productId;


    if (productName) {

        productName.value =
            product.name || "";
    }


    if (productPrice) {

        productPrice.value =
            product.price || 0;
    }


    if (productIcon) {

        productIcon.value =
            product.icon || "📦";
    }


    if (productStock) {

        productStock.value =
            product.stockStatus ||
            "In Stock";
    }


    if (productDescription) {

        productDescription.value =
            product.description || "";
    }


    /*
       Hidden input keeps the current
       image filename while editing.
    */

    if (productImage) {

        productImage.value =
            product.image || "";
    }


    /*
       Browsers don't allow file inputs
       to be pre-filled.
    */

    if (productImageFile) {

        productImageFile.value =
            "";
    }


    /*
       Display existing image.
    */

    if (
        product.image &&
        productImagePreview &&
        productImagePreviewWrapper
    ) {

        productImagePreview.src =
            `/static/assets/products/${encodeURIComponent(
                product.image
            )}`;


        productImagePreviewWrapper
            .style
            .display =
            "block";

    } else {

        hideProductImagePreview();
    }


    const submitButton =
        productForm
            ? productForm.querySelector(
                ".product-add-btn"
            )
            : null;


    if (submitButton) {

        submitButton.textContent =
            "Update Product";
    }


    if (productForm) {

        productForm.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
}


/* =====================================================
   RESET PRODUCT FORM
===================================================== */

function resetProductForm() {

    editingProductId =
        null;


    if (productForm) {

        productForm.reset();
    }


    if (productIcon) {

        productIcon.value =
            "📦";
    }


    if (productImage) {

        productImage.value =
            "";
    }


    if (productImageFile) {

        productImageFile.value =
            "";
    }


    if (productStock) {

        productStock.value =
            "In Stock";
    }


    hideProductImagePreview();


    const submitButton =
        productForm
            ? productForm.querySelector(
                ".product-add-btn"
            )
            : null;


    if (submitButton) {

        submitButton.textContent =
            "+ Add Product";
    }
}


/* =====================================================
   DELETE PRODUCT
===================================================== */

async function deleteProduct(
    productId
) {

    const product =
        allProducts.find(
            item =>
                Number(item.id) ===
                Number(productId)
        );


    if (!product) {

        alert(
            "Product could not be found."
        );

        return;
    }


    const confirmed =
        confirm(
            `Delete "${product.name}"?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/admin/products/${productId}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            if (
                response.status ===
                401
            ) {

                window.location.href =
                    "/admin/login";

                return;
            }


            throw new Error(
                data.message ||
                "Unable to delete product."
            );
        }


        if (
            editingProductId ===
            productId
        ) {

            resetProductForm();
        }


        await loadProducts();


    } catch (error) {

        console.error(
            "Delete product error:",
            error
        );


        alert(
            error.message ||
            "Unable to delete product."
        );
    }
}


/* =====================================================
   ORDER ELEMENTS
===================================================== */

const orderTableBody =
    document.getElementById(
        "orderTableBody"
    );

const emptyOrders =
    document.getElementById(
        "emptyOrders"
    );

const orderSearch =
    document.getElementById(
        "orderSearch"
    );

const orderStatusFilter =
    document.getElementById(
        "orderStatusFilter"
    );

const orderSort =
    document.getElementById(
        "orderSort"
    );

let allOrders = [];


/* =====================================================
   LOAD ORDERS
===================================================== */

async function loadOrders() {

    if (!orderTableBody) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/admin/orders"
            );


        const data =
            await response.json();


        if (!response.ok) {

            if (
                response.status === 401
            ) {

                window.location.href =
                    "/admin/login";

                return;
            }


            throw new Error(
                data.message ||
                "Unable to load orders."
            );
        }


        allOrders =
            data.orders || [];


        displayOrders();


    } catch (error) {

        console.error(
            "Order load error:",
            error
        );


        if (emptyOrders) {

            emptyOrders.textContent =
                "Unable to load customer orders.";

            emptyOrders.style.display =
                "block";
        }
    }
}


/* =====================================================
   DISPLAY ORDERS
===================================================== */

function displayOrders() {

    if (!orderTableBody) {
        return;
    }


    orderTableBody.innerHTML =
        "";


    const searchValue =
        orderSearch
            ? orderSearch.value
                .trim()
                .toLowerCase()
            : "";


    const selectedStatus =
        orderStatusFilter
            ? orderStatusFilter.value
            : "";


    const selectedSort =
        orderSort
            ? orderSort.value
            : "newest";


    let filteredOrders =
        allOrders.filter(
            function(order) {

                const searchableText =
                    `
                        ${order.orderId || ""}
                        ${order.customerName || ""}
                        ${order.phone || ""}
                        ${order.productName || ""}
                        ${order.status || ""}
                    `.toLowerCase();


                const matchesSearch =
                    searchableText.includes(
                        searchValue
                    );


                const matchesStatus =
                    !selectedStatus ||
                    order.status ===
                        selectedStatus;


                return (
                    matchesSearch &&
                    matchesStatus
                );
            }
        );


    /* =================================================
       SORT ORDERS
    ================================================= */

    filteredOrders.sort(
        function(a, b) {

            if (
                selectedSort ===
                "oldest"
            ) {

                return (
                    new Date(
                        normalizeDate(
                            a.createdAt
                        )
                    )
                    -
                    new Date(
                        normalizeDate(
                            b.createdAt
                        )
                    )
                );
            }


            if (
                selectedSort ===
                "highest"
            ) {

                return (
                    Number(
                        b.totalPrice || 0
                    )
                    -
                    Number(
                        a.totalPrice || 0
                    )
                );
            }


            if (
                selectedSort ===
                "lowest"
            ) {

                return (
                    Number(
                        a.totalPrice || 0
                    )
                    -
                    Number(
                        b.totalPrice || 0
                    )
                );
            }


            return (
                new Date(
                    normalizeDate(
                        b.createdAt
                    )
                )
                -
                new Date(
                    normalizeDate(
                        a.createdAt
                    )
                )
            );
        }
    );


    /* =================================================
       EMPTY STATE
    ================================================= */

    if (
        filteredOrders.length === 0
    ) {

        if (emptyOrders) {

            emptyOrders.textContent =
                "No customer orders found.";

            emptyOrders.style.display =
                "block";
        }

        updateOrderStats();

        return;
    }


    if (emptyOrders) {

        emptyOrders.style.display =
            "none";
    }


    /* =================================================
       CREATE ORDER ROWS
    ================================================= */

    filteredOrders.forEach(
        function(order) {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    <strong>
                        ${escapeHTML(
                            order.orderId
                        )}
                    </strong>

                    <small>
                        ${escapeHTML(
                            order.createdAt || ""
                        )}
                    </small>
                </td>


                <td>

                    ${escapeHTML(
                        order.customerName
                    )}

                    <small>
                        ${escapeHTML(
                            order.phone
                        )}
                    </small>

                </td>


                <td>

                    ${escapeHTML(
                        order.productName
                    )}

                </td>


                <td>

                    ${escapeHTML(
                        order.quantity
                    )}

                </td>


                <td>

                    ₦${formatPrice(
                        order.totalPrice
                    )}

                </td>


                <td>

                    <span
                        class="
                            admin-status
                            order-status-${statusClassName(
                                order.status
                            )}
                        "
                    >
                        ${escapeHTML(
                            order.status
                        )}
                    </span>

                </td>


                <td>

                    <select
                        class="order-status-select"
                        data-id="${escapeHTML(
                            order.orderId
                        )}"
                    >

                        <option
                            value="Pending"
                            ${
                                order.status ===
                                "Pending"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Pending
                        </option>


                        <option
                            value="Confirmed"
                            ${
                                order.status ===
                                "Confirmed"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Confirmed
                        </option>


                        <option
                            value="Ready"
                            ${
                                order.status ===
                                "Ready"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Ready
                        </option>


                        <option
                            value="Completed"
                            ${
                                order.status ===
                                "Completed"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Completed
                        </option>


                        <option
                            value="Cancelled"
                            ${
                                order.status ===
                                "Cancelled"
                                    ? "selected"
                                    : ""
                            }
                        >
                            Cancelled
                        </option>

                    </select>


                    <button
                        type="button"
                        class="order-delete-btn"
                        data-id="${escapeHTML(
                            order.orderId
                        )}"
                    >
                        Delete
                    </button>

                </td>

            `;


            orderTableBody
                .appendChild(
                    row
                );
        }
    );


    updateOrderStats();

    addOrderListeners();
}


/* =====================================================
   NORMALIZE SQLITE DATE
===================================================== */

function normalizeDate(
    dateValue
) {

    if (!dateValue) {
        return "";
    }


    return String(
        dateValue
    ).replace(
        " ",
        "T"
    );
}


/* =====================================================
   ORDER STATUS CLASS NAME
===================================================== */

function statusClassName(
    status
) {

    return String(
        status || ""
    )
        .trim()
        .toLowerCase()
        .replaceAll(
            " ",
            "-"
        );
}


/* =====================================================
   ORDER SEARCH
===================================================== */

if (orderSearch) {

    orderSearch.addEventListener(
        "input",
        function() {

            displayOrders();

        }
    );
}


/* =====================================================
   ORDER STATUS FILTER
===================================================== */

if (orderStatusFilter) {

    orderStatusFilter.addEventListener(
        "change",
        function() {

            displayOrders();

        }
    );
}


/* =====================================================
   ORDER SORT
===================================================== */

if (orderSort) {

    orderSort.addEventListener(
        "change",
        function() {

            displayOrders();

        }
    );
}


/* =====================================================
   UPDATE ORDER STATISTICS
===================================================== */

function updateOrderStats() {

    const totalOrders =
        document.getElementById(
            "totalOrders"
        );

    const pendingOrders =
        document.getElementById(
            "pendingOrders"
        );

    const completedOrders =
        document.getElementById(
            "completedOrders"
        );

    const orderRevenue =
        document.getElementById(
            "orderRevenue"
        );


    if (totalOrders) {

        totalOrders.textContent =
            allOrders.length;
    }


    if (pendingOrders) {

        pendingOrders.textContent =
            allOrders.filter(
                order =>
                    order.status ===
                    "Pending"
            ).length;
    }


    if (completedOrders) {

        completedOrders.textContent =
            allOrders.filter(
                order =>
                    order.status ===
                    "Completed"
            ).length;
    }


    if (orderRevenue) {

        const revenue =
            allOrders
                .filter(
                    order =>
                        order.status ===
                        "Completed"
                )
                .reduce(
                    function(
                        total,
                        order
                    ) {

                        return (
                            total +
                            Number(
                                order.totalPrice || 0
                            )
                        );

                    },
                    0
                );


        orderRevenue.textContent =
            `₦${formatPrice(
                revenue
            )}`;
    }

}


/* =====================================================
   ORDER ACTION LISTENERS
===================================================== */

function addOrderListeners() {

    const statusSelects =
        document.querySelectorAll(
            ".order-status-select"
        );


    const deleteButtons =
        document.querySelectorAll(
            ".order-delete-btn"
        );


    statusSelects.forEach(
        function(select) {

            select.addEventListener(
                "change",
                async function() {

                    const orderId =
                        this.dataset.id;

                    const newStatus =
                        this.value;


                    const order =
                        allOrders.find(
                            item =>
                                item.orderId ===
                                orderId
                        );


                    const oldStatus =
                        order
                            ? order.status
                            : "";


                    this.disabled =
                        true;


                    try {

                        const response =
                            await fetch(
                                `/api/admin/orders/${encodeURIComponent(
                                    orderId
                                )}/status`,
                                {

                                    method:
                                        "PUT",

                                    headers: {

                                        "Content-Type":
                                            "application/json"

                                    },

                                    body:
                                        JSON.stringify({

                                            status:
                                                newStatus

                                        })

                                }
                            );


                        const data =
                            await response.json();


                        if (!response.ok) {

                            if (
                                response.status ===
                                401
                            ) {

                                window.location.href =
                                    "/admin/login";

                                return;
                            }


                            throw new Error(
                                data.message ||
                                "Unable to update order status."
                            );
                        }


                        if (order) {

                            order.status =
                                newStatus;
                        }


                    } catch (error) {

                        console.error(
                            "Order status error:",
                            error
                        );


                        alert(
                            error.message ||
                            "Unable to update order status."
                        );


                        this.value =
                            oldStatus;


                    } finally {

                        this.disabled =
                            false;
                    }
                }
            );
        }
    );


    deleteButtons.forEach(
        function(button) {

            button.addEventListener(
                "click",
                async function() {

                    const orderId =
                        this.dataset.id;


                    const confirmed =
                        confirm(
                            `Delete order ${orderId}?`
                        );


                    if (!confirmed) {
                        return;
                    }


                    this.disabled =
                        true;


                    try {

                        const response =
                            await fetch(
                                `/api/admin/orders/${encodeURIComponent(
                                    orderId
                                )}`,
                                {
                                    method:
                                        "DELETE"
                                }
                            );


                        const data =
                            await response.json();


                        if (!response.ok) {

                            if (
                                response.status ===
                                401
                            ) {

                                window.location.href =
                                    "/admin/login";

                                return;
                            }


                            throw new Error(
                                data.message ||
                                "Unable to delete order."
                            );
                        }


                        await loadOrders();


                    } catch (error) {

                        console.error(
                            "Delete order error:",
                            error
                        );


                        alert(
                            error.message ||
                            "Unable to delete order."
                        );


                        this.disabled =
                            false;
                    }
                }
            );
        }
    );
}


/* =====================================================
   FORMAT PRICE
===================================================== */

function formatPrice(
    price
) {

    return Number(
        price || 0
    ).toLocaleString(
        "en-NG"
    );
}


/* =====================================================
   ESCAPE HTML
===================================================== */

function escapeHTML(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =====================================================
   START ADMIN DASHBOARD
===================================================== */

loadRepairs();

loadProducts();

loadOrders();