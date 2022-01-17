function IncomingHttpRequestFilter(method, uri, ip, username, httpHeaders)
    -- Only allow GET requests for non-admin users (or 'uploader'-> used for pacs2go tools' direct upload)
    -- extra: allow 'do lookup' in ORTHANC (/tools/find), as this kind of lookup is a post request, that does not alter data
    if method == 'GET' or string.find(uri,"/tools/find") ~= nil then 
        return true
    elseif username == 'admin' or username == 'uploader' then
        return true
    else
        print("no access")
        return false
    end
end


function ReceivedInstanceFilter(dicom, origin, info)
    -- Only allow incoming images if they are pseudonymized
    if dicom.PatientIdentityRemoved == 'YES' then
        print("Identity is removed")
        return true
    else
        print("You should remove the identity")
        return false
    end
end
