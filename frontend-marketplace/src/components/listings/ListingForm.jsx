// src/components/listings/ListingForm.jsx
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import Input from '../common/Input';
import Button from '../common/Button';
import Select from 'react-select';
import categoryService from '../../services/categoryService';

const RequiredIndicator = () => <span className="text-red-500 ml-1">*</span>;

const ListingForm = ({ onSubmitForm, initialData = {}, listingType = 'material', isLoading = false, apiFormError }) => {
  const { 
    register, 
    handleSubmit, 
    control, 
    watch, 
    setValue,
    reset, 
    formState: { errors, isDirty } 
  } = useForm({
    defaultValues: initialData || {},
  });

  const [imagePreview, setImagePreview] = useState(initialData?.main_image_url || initialData?.thumbnail_image_url || null);
  const [categories, setCategories] = useState([]);
  const [categoryLoading, setCategoryLoading] = useState(false);

  const imageFileKey = listingType === 'material' ? 'main_image_file' : 'thumbnail_image_file';
  const watchedImageFile = watch(imageFileKey);

  // Moved materialUnitOptions outside the return statement
  const materialUnitOptions = [
    { value: 'm', label: 'Meter (m)' }, { value: 'kg', label: 'Kilogram (kg)' },
    { value: 'sqm', label: 'Square Meter (sqm)' }, { value: 'pcs', label: 'Pieces (pcs)' },
    { value: 'yard', label: 'Yard (yd)' }, { value: 'lb', label: 'Pound (lb)' },
  ];

  useEffect(() => {
    if (initialData && Object.keys(initialData).length > 0) {
      const currentImageURL = initialData.main_image_url || initialData.thumbnail_image_url;
      const categoryDefault = initialData.category 
        ? { value: initialData.category.id, label: initialData.category.name }
        : (initialData.category_id ? { value: initialData.category_id, label: 'Loading...' } : null) ;

      reset({
        ...initialData,
        category_id: categoryDefault,
      });
      setImagePreview(currentImageURL || null);
    } else {
      reset({
        unit: 'm', // Default unit for new material
        minimum_order_quantity: 1, // Default MOQ for new material
      });
      setImagePreview(null);
    }
  }, [initialData, reset]);

  useEffect(() => {
    const fetchCats = async () => {
      setCategoryLoading(true);
      try {
        const data = await categoryService.getCategories();
        const categoryOptions = data.map(cat => ({ value: cat.id, label: cat.name }));
        setCategories(categoryOptions);

        const currentFormCategoryIdValue = control.getValues('category_id');
        let categoryIdToMatch = null;

        if (currentFormCategoryIdValue && typeof currentFormCategoryIdValue === 'object' && currentFormCategoryIdValue.value) {
            categoryIdToMatch = currentFormCategoryIdValue.value;
        } else if (typeof currentFormCategoryIdValue === 'string' || typeof currentFormCategoryIdValue === 'number') {
            categoryIdToMatch = currentFormCategoryIdValue;
        } else if (initialData?.category_id) {
             categoryIdToMatch = initialData.category_id;
        } else if (initialData?.category?.id) {
            categoryIdToMatch = initialData.category.id;
        }

        if (categoryIdToMatch) {
            const foundCat = categoryOptions.find(c => String(c.value) === String(categoryIdToMatch));
            if (foundCat && (!currentFormCategoryIdValue || currentFormCategoryIdValue.label === 'Loading...' || currentFormCategoryIdValue.label === undefined) ) {
                 setValue('category_id', foundCat, {shouldDirty: !!initialData?.id, shouldValidate: false });
            }
        }
      } catch (error) {
        console.error("Failed to fetch categories", error);
      }
      setCategoryLoading(false);
    };
    fetchCats();
  }, [initialData, control, setValue]);


  useEffect(() => {
    if (watchedImageFile && watchedImageFile.length > 0 && watchedImageFile[0] instanceof File) {
      const file = watchedImageFile[0];
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else if ((!watchedImageFile || watchedImageFile.length === 0) && (initialData?.main_image_url || initialData?.thumbnail_image_url) ) {
      setImagePreview(initialData.main_image_url || initialData.thumbnail_image_url);
    } else if (!watchedImageFile || watchedImageFile.length === 0) {
        setImagePreview(null);
    }
  }, [watchedImageFile, initialData]);


  const internalOnSubmit = (dataFromRHF) => {
    const formData = new FormData();
    const backendImageKey = listingType === 'material' ? 'main_image' : 'thumbnail_image';
    const imageFileList = dataFromRHF[imageFileKey]; 

    if (imageFileList && imageFileList.length > 0 && imageFileList[0] instanceof File) {
      const file = imageFileList[0];
      formData.append(backendImageKey, file, file.name);
    }

    Object.keys(dataFromRHF).forEach(key => {
      if (key === imageFileKey) return;
      const value = dataFromRHF[key];

      if (
        (key === 'stock_quantity' || key === 'weight_gsm' || key === 'width_cm' || key === 'lead_time_days') &&
        (value === '' || value === null || value === undefined || (typeof value === 'string' && isNaN(parseFloat(value))) )
      ) {
        return; 
      }
      
      if (key === 'category_id' && value && typeof value === 'object' && value.hasOwnProperty('value')) {
        formData.append(key, value.value);
      } else if (value !== null && value !== undefined) {
        formData.append(key, value);
      }
    });
    
    onSubmitForm(formData);
  };

  return (
    <form onSubmit={handleSubmit(internalOnSubmit)} className="space-y-6">
      {apiFormError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiFormError}</p>}

      <Input
        label={<>{listingType === 'material' ? "Material Name" : "Design Title"} <RequiredIndicator /></>}
        id={listingType === 'material' ? "name" : "title"}
        {...register(listingType === 'material' ? "name" : "title", { required: "This field is required" })}
        error={errors[listingType === 'material' ? "name" : "title"]}
      />

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description <RequiredIndicator />
        </label>
        <textarea
          id="description"
          rows="4"
          {...register("description", { required: "Description is required" })}
          className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.description ? 'border-red-500' : ''}`}
        />
        {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
      </div>
      
      <div>
        <label htmlFor="category_id_select" className="block text-sm font-medium text-gray-700 mb-1"> 
            Category <RequiredIndicator />
        </label>
        <Controller
            name="category_id"
            control={control}
            rules={{ required: "Category is required" }}
            render={({ field }) => (
              <Select
                {...field}
                options={categories}
                isLoading={categoryLoading}
                placeholder="Select a category..."
                classNamePrefix="react-select"
                className={`mt-1 react-select-container ${errors.category_id ? 'react-select-error border !border-red-500 rounded-md' : ''}`}
                inputId="category_id_select"
                isClearable
              />
            )}
        />
        {errors.category_id && <p className="mt-1 text-xs text-red-600">{errors.category_id.message || (errors.category_id.value && "Category is required")}</p>}
      </div>

      <div>
        <label htmlFor={imageFileKey} className="block text-sm font-medium text-gray-700 mb-1">
          {listingType === 'material' ? "Main Material Image" : "Thumbnail Image"} (Optional)
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="w-40 h-40 object-cover mb-2 rounded-md border" />}
        <input
          type="file"
          id={imageFileKey}
          accept="image/png, image/jpeg, image/gif"
          {...register(imageFileKey)}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>

      {listingType === 'material' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label={<>Price Per Unit <RequiredIndicator /></>}
              id="price_per_unit"
              type="number"
              step="0.01"
              {...register("price_per_unit", { required: "Price is required", valueAsNumber: true, min: {value: 0.01, message: "Price must be greater than 0"} })}
              error={errors.price_per_unit}
            />
            <div>
                <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">Unit <RequiredIndicator /></label>
                <select
                  id="unit"
                  {...register("unit", { required: "Unit is required" })}
                  className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md ${errors.unit ? 'border-red-500' : ''}`}
                  defaultValue="m"
                >
                  {materialUnitOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
                {errors.unit && <p className="mt-1 text-xs text-red-600">{errors.unit.message}</p>}
            </div>
          </div>
          <Input
            label={<>Minimum Order Quantity (MOQ) <RequiredIndicator /></>}
            id="minimum_order_quantity"
            type="number"
            step="1"
            {...register("minimum_order_quantity", { required: "MOQ is required", valueAsNumber: true, min: {value: 1, message:"MOQ must be at least 1"} })}
            error={errors.minimum_order_quantity}
            defaultValue={1}
          />
          <Input
            label="Stock Quantity (Optional)"
            id="stock_quantity"
            type="number"
            step="1"
            {...register("stock_quantity", { 
                setValueAs: v => (v === "" || v === null || v === undefined || isNaN(parseInt(v))) ? null : parseInt(v),
                min: {value: 0, message: "Stock can't be negative"}
            })}
            error={errors.stock_quantity}
          />
          <Input label="SKU (Optional)" id="sku" {...register("sku")} error={errors.sku} />
          <Input label="Composition (e.g., 100% Cotton) (Optional)" id="composition" {...register("composition")} error={errors.composition} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input label="Weight (GSM, Optional)" id="weight_gsm" type="number" {...register("weight_gsm", {setValueAs: v => (v === "" || v === null || v === undefined || isNaN(parseInt(v))) ? null : parseInt(v), min:0})} error={errors.weight_gsm} />
            <Input label="Width (cm, Optional)" id="width_cm" type="number" {...register("width_cm", {setValueAs: v => (v === "" || v === null || v === undefined || isNaN(parseInt(v))) ? null : parseInt(v), min:0})} error={errors.width_cm} />
          </div>
          <Input label="Country of Origin (Optional)" id="country_of_origin" {...register("country_of_origin")} error={errors.country_of_origin} />
          <Input label="Lead Time (days, Optional)" id="lead_time_days" type="number" {...register("lead_time_days", {setValueAs: v => (v === "" || v === null || v === undefined || isNaN(parseInt(v))) ? null : parseInt(v), min:0})} error={errors.lead_time_days} />
        </>
      )}
      
      <div className="pt-4">
        <Button type="submit" variant="primary" className="w-full md:w-auto" isLoading={isLoading} disabled={isLoading || (!isDirty && !!initialData?.id)}>
          {isLoading ? 'Saving...' : (initialData?.id ? 'Save Changes' : 'Create Listing')}
        </Button>
      </div>
    </form>
  );
};

export default ListingForm;