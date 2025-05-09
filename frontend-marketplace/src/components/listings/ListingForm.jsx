// src/components/listings/ListingForm.jsx
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import Input from '../common/Input';
import Button from '../common/Button';
// import Select from 'react-select'; // For a nicer select component if you install it
// import categoryService from '../../services/categoryService'; // If fetching categories for select

const ListingForm = ({ onSubmitForm, initialData = {}, listingType = 'material', isLoading = false }) => {
  const { register, handleSubmit, control, watch, setValue, formState: { errors, isDirty } } = useForm({
    defaultValues: initialData,
  });
  const [apiError, setApiError] = useState('');
  const [imagePreview, setImagePreview] = useState(initialData?.main_image_url || null);
  // const [categories, setCategories] = useState([]); // For category dropdown

  // useEffect(() => { // Example: Fetch categories for dropdown
  //   const fetchCats = async () => {
  //     try {
  //       const data = await categoryService.getAll(); // Assuming this service exists
  //       setCategories(data.results.map(cat => ({ value: cat.id, label: cat.name })));
  //     } catch (error) {
  //       console.error("Failed to fetch categories", error);
  //     }
  //   };
  //   fetchCats();
  // }, []);

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setValue('main_image_file', file, { shouldDirty: true }); // Store actual file
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const internalOnSubmit = (data) => {
    setApiError('');
    const formData = new FormData();

    // Append all fields. For files, append the file object.
    Object.keys(data).forEach(key => {
      if (key === 'main_image_file' && data[key] instanceof File) {
        formData.append('main_image', data[key], data[key].name); // Backend expects 'main_image'
      } else if (key === 'tag_ids' && Array.isArray(data[key])) { // Example for tags if using react-select like
        data[key].forEach(tagId => formData.append('tag_ids', tagId));
      } else if (data[key] !== null && data[key] !== undefined && key !== 'main_image_file') {
        formData.append(key, data[key]);
      }
    });
    
    // If initialData had an image and no new one is uploaded,
    // backend might need to know not to clear it. This logic depends on PATCH behavior.
    // For CREATE, this is simpler.

    onSubmitForm(formData); // Pass FormData to parent submit handler
  };

  const isMaterial = listingType === 'material';
  const isDesign = listingType === 'design';

  const materialUnitOptions = [ // From your Material model
    { value: 'm', label: 'Meter (m)' },
    { value: 'kg', label: 'Kilogram (kg)' },
    { value: 'sqm', label: 'Square Meter (sqm)' },
    { value: 'pcs', label: 'Pieces (pcs)' },
    { value: 'yard', label: 'Yard (yd)' },
    { value: 'lb', label: 'Pound (lb)' },
  ];

  return (
    <form onSubmit={handleSubmit(internalOnSubmit)} className="space-y-6">
      {apiError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiError}</p>}

      <Input
        label={isMaterial ? "Material Name" : "Design Title"}
        id={isMaterial ? "name" : "title"}
        {...register(isMaterial ? "name" : "title", { required: "This field is required" })}
        error={errors[isMaterial ? "name" : "title"]}
      />

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          id="description"
          rows="4"
          {...register("description", { required: "Description is required" })}
          className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.description ? 'border-red-500' : ''}`}
        />
        {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
      </div>
      
      {/* TODO: Category Select - placeholder for now */}
      <Input
        label="Category ID (temp)"
        id="category_id"
        placeholder="Enter existing category ID (e.g., UUID from admin)"
        {...register("category_id")} // Make this a proper select later
        error={errors.category_id}
      />
      {/* <Controller
        name="category_id"
        control={control}
        rules={{ required: "Category is required" }}
        render={({ field }) => (
          <Select // react-select example
            {...field}
            options={categories}
            placeholder="Select a category..."
            classNamePrefix="react-select"
          />
        )}
      />
      {errors.category_id && <p className="mt-1 text-xs text-red-600">{errors.category_id.message}</p>} */}


      <div>
        <label htmlFor="main_image" className="block text-sm font-medium text-gray-700 mb-1">
          {isMaterial ? "Main Material Image" : "Thumbnail Image"}
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="w-40 h-40 object-cover mb-2 rounded-md border" />}
        <input
          type="file"
          id="main_image" // This input doesn't need to be registered with RHF directly if using setValue
          accept="image/*"
          onChange={handleImageChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {/* RHF doesn't directly validate file inputs easily without custom logic or Controller */}
      </div>

      {isMaterial && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Price Per Unit"
              id="price_per_unit"
              type="number"
              step="0.01"
              {...register("price_per_unit", { required: "Price is required", valueAsNumber: true, min: {value: 0, message: "Price must be positive"} })}
              error={errors.price_per_unit}
            />
            <div>
                <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
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
            label="Minimum Order Quantity (MOQ)"
            id="minimum_order_quantity"
            type="number"
            step="1"
            {...register("minimum_order_quantity", { valueAsNumber: true, min: {value: 1, message:"MOQ must be at least 1"} })}
            error={errors.minimum_order_quantity}
            defaultValue={1}
          />
          <Input
            label="Stock Quantity (optional)"
            id="stock_quantity"
            type="number"
            step="1"
            {...register("stock_quantity", { valueAsNumber: true, min: {value: 0, message: "Stock can't be negative"} })}
            error={errors.stock_quantity}
          />
          <Input label="SKU (optional)" id="sku" {...register("sku")} error={errors.sku} />
          <Input label="Composition (e.g., 100% Cotton)" id="composition" {...register("composition")} error={errors.composition} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input label="Weight (GSM, optional)" id="weight_gsm" type="number" {...register("weight_gsm", {valueAsNumber:true, min:0})} error={errors.weight_gsm} />
            <Input label="Width (cm, optional)" id="width_cm" type="number" {...register("width_cm", {valueAsNumber:true, min:0})} error={errors.width_cm} />
          </div>
          <Input label="Country of Origin (optional)" id="country_of_origin" {...register("country_of_origin")} error={errors.country_of_origin} />
          <Input label="Lead Time (days, optional)" id="lead_time_days" type="number" {...register("lead_time_days", {valueAsNumber:true, min:0})} error={errors.lead_time_days} />
        </>
      )}

      {isDesign && (
        <>
          <Input
            label="Price (optional)"
            id="price"
            type="number"
            step="0.01"
            {...register("price", { valueAsNumber: true, min: {value: 0, message: "Price must be positive"} })}
            error={errors.price}
          />
          <div>
            <label htmlFor="licensing_terms" className="block text-sm font-medium text-gray-700 mb-1">Licensing Terms</label>
            <textarea
              id="licensing_terms"
              rows="3"
              {...register("licensing_terms")}
              className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.licensing_terms ? 'border-red-500' : ''}`}
            />
            {errors.licensing_terms && <p className="mt-1 text-xs text-red-600">{errors.licensing_terms.message}</p>}
          </div>
           <Input label="Design Files Link (Secure URL)" id="design_files_link" type="url" {...register("design_files_link")} error={errors.design_files_link} />
        </>
      )}
      
      {/* TODO: Tags input (e.g., using react-select Creatable or a simple comma-separated input) */}
      {/* TODO: Certifications input (multi-select or similar) */}

      <div className="pt-4">
        <Button type="submit" variant="primary" className="w-full md:w-auto" isLoading={isLoading} disabled={isLoading || !isDirty}>
          {isLoading ? 'Saving...' : (initialData?.id ? 'Save Changes' : 'Create Listing')}
        </Button>
      </div>
    </form>
  );
};

export default ListingForm;