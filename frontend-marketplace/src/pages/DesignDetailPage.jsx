// src/pages/DesignDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import productService from '../services/productService';
import Loader from '../components/common/Loader';
import Button from '../components/common/Button';
import { formatDate, formatCurrency } from '../utils/formatters';
import { MessageCircle, FolderKanban, Tag as TagIcon } from 'lucide-react'; // Example icons

const DesignDetailPage = () => {
  const { slug } = useParams();
  const [design, setDesign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDesign = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await productService.getDesignBySlug(slug);
        setDesign(data);
      } catch (err) {
        setError('Failed to fetch design details.');
        console.error(err);
      }
      setLoading(false);
    };
    if (slug) {
      fetchDesign();
    }
  }, [slug]);

  if (loading) return <Loader text="Loading design details..." />;
  if (error) return <p className="text-center text-red-500 p-10 bg-red-50 rounded-md">{error}</p>;
  if (!design) return <p className="text-center text-slate-600 p-10">Design not found.</p>;

  return (
    <div className="container-mx py-8">
      <div className="grid lg:grid-cols-3 gap-8 bg-white p-6 rounded-lg shadow-xl">
        {/* Main Content Column */}
        <div className="lg:col-span-2">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-950 mb-2">{design.title}</h1>
          <p className="text-sm text-slate-500 mb-4">
            Designed by: <Link to={`/profiles/${design.designer?.username}`} className="text-teal-700 hover:underline">{design.designer?.username || 'N/A'}</Link>
          </p>
          
          <div className="mb-6 aspect-w-16 aspect-h-9 rounded-lg overflow-hidden shadow-md">
            <img
              src={design.thumbnail_image_url || design.main_image_url || `https://via.placeholder.com/800x450?text=${encodeURIComponent(design.title)}`}
              alt={design.title}
              className="w-full h-full object-cover"
            />
          </div>
           {/* TODO: Image gallery for more design images if applicable */}

          <div className="prose max-w-none text-slate-700 mb-6 leading-relaxed">
            <p>{design.description || "No description available."}</p>
          </div>

          {design.licensing_terms && (
            <div className="mb-6 p-4 bg-orange-50 rounded-md border border-orange-200">
              <h3 className="text-md font-semibold text-orange-700 mb-1">Licensing Terms</h3>
              <p className="text-sm text-slate-600 whitespace-pre-line">{design.licensing_terms}</p>
            </div>
          )}

          {design.design_files_link && (
             <div className="mb-6">
                <Button variant="primary" className="bg-teal-800 hover:bg-teal-700" onClick={() => window.open(design.design_files_link, '_blank')}>
                    Access Design Files (Link)
                </Button>
                <p className="text-xs text-slate-500 mt-1">Note: File access may require purchase or agreement.</p>
             </div>
          )}

          {/* Tech Packs - Assuming design.tech_packs is an array from serializer */}
          {design.tech_packs && design.tech_packs.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-slate-700 mb-2 flex items-center">
                <FolderKanban size={20} className="mr-2 text-teal-700" /> Technical Packs
              </h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 pl-2">
                {design.tech_packs.map(tp => (
                  <li key={tp.id}>
                    <a href={tp.file} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:underline">
                      Tech Pack {tp.version ? `(v${tp.version})` : ''} - {tp.notes ? truncateText(tp.notes, 30) : 'View File'}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Sidebar Column */}
        <aside className="lg:col-span-1 space-y-6">
          {design.price !== null && design.price !== undefined && (
            <div className="p-6 bg-teal-50 rounded-lg border border-teal-200 shadow">
              <p className="text-3xl font-bold text-teal-800 text-center">
                {formatCurrency(design.price, design.currency || 'USD')}
              </p>
              <p className="text-xs text-teal-600 text-center">One-time purchase or license fee</p>
              <Button variant="primary" size="lg" className="w-full mt-4 bg-teal-700 hover:bg-teal-600">
                Purchase / Inquire
              </Button>
            </div>
          )}

          <div className="p-4 bg-slate-50 rounded-lg border">
            <h3 className="text-md font-semibold text-slate-700 mb-2">Designer</h3>
             {/* TODO: Small designer profile card component */}
            <p className="text-sm text-slate-600">{design.designer?.profile?.company_name || design.designer?.username}</p>
            <Link to={`/profiles/${design.designer?.username}`}>
                <Button variant="outline" size="sm" className="mt-2 w-full text-teal-700 border-teal-600 hover:bg-teal-50">View Designer Profile</Button>
            </Link>
          </div>
          
          {design.tags && design.tags.length > 0 && (
            <div className="p-4 bg-slate-50 rounded-lg border">
                <h3 className="text-md font-semibold text-slate-700 mb-3 flex items-center">
                    <TagIcon size={18} className="mr-2 text-slate-500" /> Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                    {design.tags.map(tag => (
                        <span key={tag.id || tag.slug} className="px-2 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">
                            {tag.name}
                        </span>
                    ))}
                </div>
            </div>
          )}

          {/* Add to Cart / Contact Designer / Request Collaboration actions */}
          <div className="space-y-3">
            <Button variant="outline" className="w-full text-teal-700 border-teal-600 hover:bg-teal-50 flex items-center justify-center">
                <MessageCircle size={18} className="mr-2" /> Contact Designer
            </Button>
            {/* Add other relevant actions */}
          </div>
        </aside>
      </div>
      {/* TODO: Reviews and Ratings Section for Designs */}
    </div>
  );
};

export default DesignDetailPage;