// import { useState } from 'react'
// import viteLogo from '/vite.svg'

import UploadForm from "./lib/UploadForm"

function App() {

  return (
    <div className="flex flex-col text-center justify-center bg-gray-900 h-dvh">
      <h1 className="text-4xl text-gray-50">Welcome Candidate</h1>
      <h2 className="text-white pt-10">Upload your CV in pdf format to below form.</h2>
      <h3 className="text-4xl"></h3>
      <UploadForm />
    </div>
  )
}

export default App
