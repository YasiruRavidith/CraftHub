// src/components/common/Pagination.jsx
import React from 'react';
import Button from './Button';

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  if (totalPages <= 1) {
    return null;
  }

  const pageNumbers = [];
  for (let i = 1; i <= totalPages; i++) {
    pageNumbers.push(i);
  }

  // Basic logic for displaying a limited number of page buttons
  const maxPageButtons = 5;
  let startPage, endPage;
  if (totalPages <= maxPageButtons) {
    startPage = 1;
    endPage = totalPages;
  } else {
    if (currentPage <= Math.ceil(maxPageButtons / 2)) {
      startPage = 1;
      endPage = maxPageButtons;
    } else if (currentPage + Math.floor(maxPageButtons / 2) >= totalPages) {
      startPage = totalPages - maxPageButtons + 1;
      endPage = totalPages;
    } else {
      startPage = currentPage - Math.floor(maxPageButtons / 2);
      endPage = currentPage + Math.floor(maxPageButtons / 2);
    }
  }

  const pagesToDisplay = pageNumbers.slice(startPage - 1, endPage);


  return (
    <nav className="flex items-center justify-center space-x-1 mt-8" aria-label="Pagination">
      <Button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        variant="outline"
        size="sm"
        className="px-3"
      >
        Previous
      </Button>

      {startPage > 1 && (
        <>
          <Button onClick={() => onPageChange(1)} variant="ghost" size="sm" className="px-3">1</Button>
          {startPage > 2 && <span className="px-3 py-1 text-sm">...</span>}
        </>
      )}

      {pagesToDisplay.map((number) => (
        <Button
          key={number}
          onClick={() => onPageChange(number)}
          variant={currentPage === number ? 'primary' : 'ghost'}
          size="sm"
          className="px-3"
        >
          {number}
        </Button>
      ))}

      {endPage < totalPages && (
        <>
          {endPage < totalPages -1 && <span className="px-3 py-1 text-sm">...</span>}
          <Button onClick={() => onPageChange(totalPages)} variant="ghost" size="sm" className="px-3">{totalPages}</Button>
        </>
      )}


      <Button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        variant="outline"
        size="sm"
        className="px-3"
      >
        Next
      </Button>
    </nav>
  );
};

export default Pagination;